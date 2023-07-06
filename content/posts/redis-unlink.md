---
title: redis unlink 释放大key
date: 2020-01-24 11:37:05
tags: [redis]
categories: [redis]
keywords: [redis unlink]
description: redis 4.0 以后增加unlink命令，高效释放大key。
---

# 背景

redis 单线程模型设计简单、高效。但是一个长耗时操作就会拖住redis服务器性能，在操作完成之前不能处理其他命令请求。
典型的耗时操作是删除大key。当被删除的 key 是 list、set、sorted set 或 hash 类型时，时间复杂度为 O(M)，其中 M 是 key 中包含的元素的个数。

为了优化redis删除大key性能，redis 4.0提供了unlink命令。
<!-- more -->

以下代码基于redis 5.0。

# delete

## 源码分析

原来的delete命令使用`dbSyncDelete`。见`db.c`
```cpp
/* Delete a key, value, and associated expiration entry if any, from the DB */
int dbSyncDelete(redisDb *db, robj *key) {
    /* Deleting an entry from the expires dict will not free the sds of
     * the key, because it is shared with the main dictionary. */
    if (dictSize(db->expires) > 0) dictDelete(db->expires,key->ptr);
    if (dictDelete(db->dict,key->ptr) == DICT_OK) {
        if (server.cluster_enabled) slotToKeyDel(key);
        return 1;
    } else {
        return 0;
    }
}
```

底层依赖`dict.c`的`dictDelete()`。当list、set、zset、hash类型包含的元素很多，同步的循环删除会耗费大量时间。
```cpp
/* Search and remove an element */
static int dictDelete(dict *ht, const void *key) {
    unsigned int h;
    dictEntry *de, *prevde;

    if (ht->size == 0)
        return DICT_ERR;
    h = dictHashKey(ht, key) & ht->sizemask;
    de = ht->table[h];

    prevde = NULL;
    while(de) {
        if (dictCompareHashKeys(ht,key,de->key)) {
            /* Unlink the element from the list */
            if (prevde)
                prevde->next = de->next;
            else
                ht->table[h] = de->next;

            dictFreeEntryKey(ht,de);
            dictFreeEntryVal(ht,de);
            free(de);
            ht->used--;
            return DICT_OK;
        }
        prevde = de;
        de = de->next;
    }
    return DICT_ERR; /* not found */
}
```

## redis 4之前删除大key

因为一次同步删除大key会造成长时间阻塞，所以要分批删除，每次删除一小部分，减少单次阻塞时间。

# unlink

redis 4.0 unlink的思路是：仅将keys从keyspace元数据中删除，真正的删除会在后续异步操作。

unlink的核心操作见：`lazyfree.c`中的`dbAsyncDelete()`。
1. 当entry数量很少，异步回收速度不如同步回收快。因此当entry数量大于`LAZYFREE_THRESHOLD`才触发异步回收。
2. 异步回收的原理是创建后台任务，并且把val链表添加进去（`bioCreateBackgroundJob`）

```cpp
#define LAZYFREE_THRESHOLD 64
int dbAsyncDelete(redisDb *db, robj *key) {
    /* Deleting an entry from the expires dict will not free the sds of
     * the key, because it is shared with the main dictionary. */
    if (dictSize(db->expires) > 0) dictDelete(db->expires,key->ptr);

    /* If the value is composed of a few allocations, to free in a lazy way
     * is actually just slower... So under a certain limit we just free
     * the object synchronously. */
    dictEntry *de = dictUnlink(db->dict,key->ptr);
    if (de) {
        robj *val = dictGetVal(de);
        size_t free_effort = lazyfreeGetFreeEffort(val);

        /* If releasing the object is too much work, do it in the background
         * by adding the object to the lazy free list.
         * Note that if the object is shared, to reclaim it now it is not
         * possible. This rarely happens, however sometimes the implementation
         * of parts of the Redis core may call incrRefCount() to protect
         * objects, and then call dbDelete(). In this case we'll fall
         * through and reach the dictFreeUnlinkedEntry() call, that will be
         * equivalent to just calling decrRefCount(). */
        if (free_effort > LAZYFREE_THRESHOLD && val->refcount == 1) {
            atomicIncr(lazyfree_objects,1);
            bioCreateBackgroundJob(BIO_LAZY_FREE,val,NULL,NULL);
            dictSetVal(db->dict,de,NULL);
        }
    }

    /* Release the key-val pair, or just the key if we set the val
     * field to NULL in order to lazy free it later. */
    if (de) {
        dictFreeUnlinkedEntry(db->dict,de);
        if (server.cluster_enabled) slotToKeyDel(key);
        return 1;
    } else {
        return 0;
    }
}    
```

`bio.c` 创建后台任务，使用mutext lock保证对链表的线程安全操作。
```cpp
void bioCreateBackgroundJob(int type, void *arg1, void *arg2, void *arg3) {
    struct bio_job *job = zmalloc(sizeof(*job));

    job->time = time(NULL);
    job->arg1 = arg1;
    job->arg2 = arg2;
    job->arg3 = arg3;
    pthread_mutex_lock(&bio_mutex[type]);
    listAddNodeTail(bio_jobs[type],job);
    bio_pending[type]++;
    pthread_cond_signal(&bio_newjob_cond[type]);
    pthread_mutex_unlock(&bio_mutex[type]);
}
```

`dict.c`的`dictUnlink()`从dict中删除一个key、但不进行底层value的释放。
稍后使用`dictFreeUnlinkedEntry()`进行释放。
```cpp
/* Remove an element from the table, but without actually releasing
 * the key, value and dictionary entry. The dictionary entry is returned
 * if the element was found (and unlinked from the table), and the user
 * should later call `dictFreeUnlinkedEntry()` with it in order to release it.
 * Otherwise if the key is not found, NULL is returned.
 *
 * This function is useful when we want to remove something from the hash
 * table but want to use its value before actually deleting the entry.
 * Without this function the pattern would require two lookups:
 *
 *  entry = dictFind(...);
 *  // Do something with entry
 *  dictDelete(dictionary,entry);
 *
 * Thanks to this function it is possible to avoid this, and use
 * instead:
 *
 * entry = dictUnlink(dictionary,entry);
 * // Do something with entry
 * dictFreeUnlinkedEntry(entry); // <- This does not need to lookup again.
 */
dictEntry *dictUnlink(dict *ht, const void *key) {
    return dictGenericDelete(ht,key,1);
}
```

# 小结

- key 的自然过期和手动删除，都会阻塞 Redis。
- 尽量从业务上避免 Redis 大 Key，无论从性能角度（hash成本）还是过期删除成本角度，都会比较高。
- redis 4之前删除大key，应该使用分批删除方式，减少单次阻塞时间。
- reids 4以后尽量使用 unlink 代替 delete 删除大 key。
- 当元素少于`LAZYFREE_THRESHOLD`(默认64)，unlink直接使用同步删除。

# 参考

- [UNLINK key [key ...]](https://redis.io/commands/unlink)
- [Is the UNLINK command always better than DEL command?](https://stackoverflow.com/questions/45818371/is-the-unlink-command-always-better-than-del-command)