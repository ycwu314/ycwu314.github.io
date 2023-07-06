---
title: linux localtime和timezone
date: 2020-05-08 20:46:15
tags: [linux]
categories: [linux]
keywords: [/etc/localtime, /etc/timezone]
description: /etc/localtime是用来描述本机时间，而 /etc/timezone是用来描述本机所属的时区。
---

折腾alpine，遇到时区问题，于是整理linux的localtime和timezone。
<!-- more -->

# localtime vs timezone

/etc/localtime是用来描述本机时间，而/etc/timezone是用来描述本机所属的时区。
修改时区
```
echo 'Asia/Shanghai' > /etc/timezone
```

localtime影响linux date命令。
timezone影响java Date类型。

修改时间，建议使用软链接方式：
```
ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
```

# java TimeZone

上面提到`/etc/timezone`影响java的Date行为。java获取timezone的优先级，参见`TimeZone.java`：
1. 用户指定的`user.timezone`
2. 系统的timezone，通过navtive方法获取。访问`TZ`环境变量、`/etc/timezone`等
3. GMT

```java
    /**
     * Gets the platform defined TimeZone ID.
     **/
    private static native String getSystemTimeZoneID(String javaHome);

    private static synchronized TimeZone setDefaultZone() {
        TimeZone tz;
        // get the time zone ID from the system properties
        String zoneID = AccessController.doPrivileged(
                new GetPropertyAction("user.timezone"));

        // if the time zone ID is not set (yet), perform the
        // platform to Java time zone ID mapping.
        if (zoneID == null || zoneID.isEmpty()) {
            String javaHome = AccessController.doPrivileged(
                    new GetPropertyAction("java.home"));
            try {
                zoneID = getSystemTimeZoneID(javaHome);
                if (zoneID == null) {
                    zoneID = GMT_ID;
                }
            } catch (NullPointerException e) {
                zoneID = GMT_ID;
            }
        }

        // Get the time zone for zoneID. But not fall back to
        // "GMT" here.
        tz = getTimeZone(zoneID, false);

        if (tz == null) {
            // If the given zone ID is unknown in Java, try to
            // get the GMT-offset-based time zone ID,
            // a.k.a. custom time zone ID (e.g., "GMT-08:00").
            String gmtOffsetID = getSystemGMTOffsetID();
            if (gmtOffsetID != null) {
                zoneID = gmtOffsetID;
            }
            tz = getTimeZone(zoneID, true);
        }
        assert tz != null;

        final String id = zoneID;
        AccessController.doPrivileged(new PrivilegedAction<Void>() {
            @Override
                public Void run() {
                    System.setProperty("user.timezone", id);
                    return null;
                }
            });

        defaultTimeZone = tz;
        return tz;
    }
```

对应的源文件`src/share/native/java/util/TimeZone.c`： 
```cpp
Java_java_util_TimeZone_getSystemTimeZoneID(JNIEnv *env, jclass ign,
                                            jstring java_home, jstring country)
{
    const char *cname;
    const char *java_home_dir;
    char *javaTZ;

    if (java_home == NULL)
        return NULL;

    java_home_dir = JNU_GetStringPlatformChars(env, java_home, 0);
    if (java_home_dir == NULL)
        return NULL;

    if (country != NULL) {
        cname = JNU_GetStringPlatformChars(env, country, 0);
        /* ignore error cases for cname */
    } else {
        cname = NULL;
    }

    /*
     * Invoke platform dependent mapping function
     */
    javaTZ = findJavaTZ_md(java_home_dir, cname);

    free((void *)java_home_dir);
    if (cname != NULL) {
        free((void *)cname);
    }

    if (javaTZ != NULL) {
        jstring jstrJavaTZ = JNU_NewStringPlatform(env, javaTZ);
        free((void *)javaTZ);
        return jstrJavaTZ;
    }
    return NULL;
}
```
关键是`findJavaTZ_md()`，是一个平台相关的实现。
打开一个看看：[/src/solaris/native/java/util/TimeZone_md.c](http://hg.openjdk.java.net/jdk8/jdk8/jdk/file/00cd9dc3c2b5/src/solaris/native/java/util/TimeZone_md.c)
```cpp
/*
 * findJavaTZ_md() maps platform time zone ID to Java time zone ID
 * using <java_home>/lib/tzmappings. If the TZ value is not found, it
 * trys some libc implementation dependent mappings. If it still
 * can't map to a Java time zone ID, it falls back to the GMT+/-hh:mm
 * form. `country', which can be null, is not used for UNIX platforms.
 */
/*ARGSUSED1*/
char *
findJavaTZ_md(const char *java_home_dir, const char *country)
{
    char *tz;
    char *javatz = NULL;
    char *freetz = NULL;

    tz = getenv("TZ");

#ifdef __linux__
    if (tz == NULL) {
#else
#ifdef __solaris__
    if (tz == NULL || *tz == '\0') {
#endif
#endif
        tz = getPlatformTimeZoneID();
        freetz = tz;
    }

    if (tz != NULL) {
        if (*tz == ':') {
            tz++;
        }
#ifdef __linux__
        /*
         * Ignore "posix/" prefix.
         */
        if (strncmp(tz, "posix/", 6) == 0) {
            tz += 6;
        }
#endif
        javatz = strdup(tz);
        if (freetz != NULL) {
            free((void *) freetz);
        }
    }
    return javatz;
}


/*
 * Performs libc implementation specific mapping and returns a zone ID
 * if found. Otherwise, NULL is returned.
 */
static char *
getPlatformTimeZoneID()
{
    struct stat statbuf;
    char *tz = NULL;
    FILE *fp;
    int fd;
    char *buf;
    size_t size;

    /*
     * Try reading the /etc/timezone file for Debian distros. There's
     * no spec of the file format available. This parsing assumes that
     * there's one line of an Olson tzid followed by a '\n', no
     * leading or trailing spaces, no comments.
     */
    if ((fp = fopen(ETC_TIMEZONE_FILE, "r")) != NULL) {
        char line[256];

        if (fgets(line, sizeof(line), fp) != NULL) {
            char *p = strchr(line, '\n');
            if (p != NULL) {
                *p = '\0';
            }
            if (strlen(line) > 0) {
                tz = strdup(line);
            }
        }
        (void) fclose(fp);
        if (tz != NULL) {
            return tz;
        }
    }

    /*
     * Next, try /etc/localtime to find the zone ID.
     */
    if (lstat(DEFAULT_ZONEINFO_FILE, &statbuf) == -1) {
        return NULL;
    }

    /*
     * If it's a symlink, get the link name and its zone ID part. (The
     * older versions of timeconfig created a symlink as described in
     * the Red Hat man page. It was changed in 1999 to create a copy
     * of a zoneinfo file. It's no longer possible to get the zone ID
     * from /etc/localtime.)
     */
    if (S_ISLNK(statbuf.st_mode)) {
        char linkbuf[PATH_MAX+1];
        int len;

        if ((len = readlink(DEFAULT_ZONEINFO_FILE, linkbuf, sizeof(linkbuf)-1)) == -1) {
            jio_fprintf(stderr, (const char *) "can't get a symlink of %s\n",
                        DEFAULT_ZONEINFO_FILE);
            return NULL;
        }
        linkbuf[len] = '\0';
        tz = getZoneName(linkbuf);
        if (tz != NULL) {
            tz = strdup(tz);
        }
        return tz;
    }

    /*
     * If it's a regular file, we need to find out the same zoneinfo file
     * that has been copied as /etc/localtime.
     */
    size = (size_t) statbuf.st_size;
    buf = (char *) malloc(size);
    if (buf == NULL) {
        return NULL;
    }
    if ((fd = open(DEFAULT_ZONEINFO_FILE, O_RDONLY)) == -1) {
        free((void *) buf);
        return NULL;
    }

    if (read(fd, buf, size) != (ssize_t) size) {
        (void) close(fd);
        free((void *) buf);
        return NULL;
    }
    (void) close(fd);

    tz = findZoneinfoFile(buf, size, ZONEINFO_DIR);
    free((void *) buf);
    return tz;
}
```

# zdump命令

>Zdump 对命令行中的每一个 zonename 输出其当前时间。

```
[root@host143 Asia]#  zdump America/New_York PRC
America/New_York  Fri May  8 09:39:35 2020 EDT
PRC               Fri May  8 21:39:35 2020 CST
```

# tzselect命令

tzselect提供交互引导方式设置时区。
```
[root@host143 Asia]# tzselect
Please identify a location so that time zone rules can be set correctly.
Please select a continent or ocean.
 1) Africa
 2) Americas
 3) Antarctica
 4) Arctic Ocean
 5) Asia
 6) Atlantic Ocean
 7) Australia
 8) Europe
 9) Indian Ocean
10) Pacific Ocean
11) none - I want to specify the time zone using the Posix TZ format.
#? 5
Please select a country.
 1) Afghanistan		  18) Israel		    35) Palestine
 2) Armenia		  19) Japan		    36) Philippines
 3) Azerbaijan		  20) Jordan		    37) Qatar
 4) Bahrain		  21) Kazakhstan	    38) Russia
 5) Bangladesh		  22) Korea (North)	    39) Saudi Arabia
 6) Bhutan		  23) Korea (South)	    40) Singapore
 7) Brunei		  24) Kuwait		    41) Sri Lanka
 8) Cambodia		  25) Kyrgyzstan	    42) Syria
 9) China		  26) Laos		    43) Taiwan
10) Cyprus		  27) Lebanon		    44) Tajikistan
11) East Timor		  28) Macau		    45) Thailand
12) Georgia		  29) Malaysia		    46) Turkmenistan
13) Hong Kong		  30) Mongolia		    47) United Arab Emirates
14) India		  31) Myanmar (Burma)	    48) Uzbekistan
15) Indonesia		  32) Nepal		    49) Vietnam
16) Iran		  33) Oman		    50) Yemen
17) Iraq		  34) Pakistan
#? 9
Please select one of the following time zone regions.
1) Beijing Time
2) Xinjiang Time
#? 1

The following information has been given:

	China
	Beijing Time

Therefore TZ='Asia/Shanghai' will be used.
Local time is now:	Fri May  8 21:42:41 CST 2020.
Universal Time is now:	Fri May  8 13:42:41 UTC 2020.
Is the above information OK?
1) Yes
2) No
#? 

```