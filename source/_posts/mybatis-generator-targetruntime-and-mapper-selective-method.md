---
title: mybatis generator 生成selective mapper方法
date: 2019-11-21 10:42:29
tags: [mybatis, java]
categories: [java]
keywords: [mybatis generator targetruntime]
description: mybatis generator targetruntime为MyBatis3Simple，不会生成xxxSelective mapper方法。
---

# 背景

项目使用mybatis generator生成entity、mapper类。拷贝祖传配置，执行后发现没有生成xxxSelective方法，很不习惯。
一开始以为是table没有指定相应selective方法，于是打开mybatis generator的dtd文件，发现并没有关于生成selective的选项：
<!-- more -->
```xml
<!ATTLIST table
  catalog CDATA #IMPLIED
  schema CDATA #IMPLIED
  tableName CDATA #REQUIRED
  alias CDATA #IMPLIED
  domainObjectName CDATA #IMPLIED
  mapperName CDATA #IMPLIED
  sqlProviderName CDATA #IMPLIED
  enableInsert CDATA #IMPLIED
  enableSelectByPrimaryKey CDATA #IMPLIED
  enableSelectByExample CDATA #IMPLIED
  enableUpdateByPrimaryKey CDATA #IMPLIED
  enableDeleteByPrimaryKey CDATA #IMPLIED
  enableDeleteByExample CDATA #IMPLIED
  enableCountByExample CDATA #IMPLIED
  enableUpdateByExample CDATA #IMPLIED
  selectByPrimaryKeyQueryId CDATA #IMPLIED
  selectByExampleQueryId CDATA #IMPLIED
  modelType CDATA #IMPLIED
  escapeWildcards CDATA #IMPLIED
  delimitIdentifiers CDATA #IMPLIED
  delimitAllColumns CDATA #IMPLIED>
```

后来经同事指出是targetRuntime的不同引起的。这次项目的配置是
```xml
<context id="mysql"  targetRuntime="MyBatis3Simple" >
```
以前的配置是
```xml
<context id="mysql"  targetRuntime="MyBatis3" >
```

# mybatis generator targetRuntime

{% asset_img mybatis-generator-introspected-table.png mybatis-generator-introspected-table %}

IntrospectedTable定义了2种基本targetRuntime
```java
public abstract class IntrospectedTable {

    public enum TargetRuntime {
        MYBATIS3,
        MYBATIS3_DSQL
    }
    // more code
}
```
MYBATIS3对应 IntrospectedTableMyBatis3Impl、 IntrospectedTableMyBatis3SimpleImpl。
MYBATIS3_DSQL对应IntrospectedTableMyBatis3DynamicSqlImplV1和V2(不是这次的讨论重点)。

IntrospectedTableMyBatis3SimpleImpl继承于IntrospectedTableMyBatis3Impl。
IntrospectedTableMyBatis3Impl提供了createJavaClientGenerator() 默认实现，并且可以被子类覆盖，这是选择java代码生成器，生成不同的mapper方法。

{% asset_img slug abstract-generator.png abstract-generator %}

AbstractJavaGenerator定义了getCompilationUnits()，获取要生成的模板单元（主要是各种mapper方法）
```java
public abstract class AbstractJavaGenerator extends AbstractGenerator {
    public abstract List<CompilationUnit> getCompilationUnits();
}
```
接下来再看看不同targetRuntime选择的code generator。

## IntrospectedTableMyBatis3Impl

```java
    protected AbstractJavaClientGenerator createJavaClientGenerator() {
        if (context.getJavaClientGeneratorConfiguration() == null) {
            return null;
        }
        
        String type = context.getJavaClientGeneratorConfiguration()
                .getConfigurationType();

        AbstractJavaClientGenerator javaGenerator;
        if ("XMLMAPPER".equalsIgnoreCase(type)) { //$NON-NLS-1$
            javaGenerator = new JavaMapperGenerator(getClientProject());
        } else if ("MIXEDMAPPER".equalsIgnoreCase(type)) { //$NON-NLS-1$
            javaGenerator = new MixedClientGenerator(getClientProject());
        } else if ("ANNOTATEDMAPPER".equalsIgnoreCase(type)) { //$NON-NLS-1$
            javaGenerator = new AnnotatedClientGenerator(getClientProject());
        } else if ("MAPPER".equalsIgnoreCase(type)) { //$NON-NLS-1$
            javaGenerator = new JavaMapperGenerator(getClientProject());
        } else {
            javaGenerator = (AbstractJavaClientGenerator) ObjectFactory
                    .createInternalObject(type);
        }

        return javaGenerator;
    }
```
打开其中一个生成器，比如JavaMapperGenerator
```java
    @Override
    public List<CompilationUnit> getCompilationUnits() {
        //
        addCountByExampleMethod(interfaze);
        addDeleteByExampleMethod(interfaze);
        addDeleteByPrimaryKeyMethod(interfaze);
        addInsertMethod(interfaze);
        addInsertSelectiveMethod(interfaze);
        addSelectByExampleWithBLOBsMethod(interfaze);
        addSelectByExampleWithoutBLOBsMethod(interfaze);
        addSelectByPrimaryKeyMethod(interfaze);
        addUpdateByExampleSelectiveMethod(interfaze);
        addUpdateByExampleWithBLOBsMethod(interfaze);
        addUpdateByExampleWithoutBLOBsMethod(interfaze);
        addUpdateByPrimaryKeySelectiveMethod(interfaze);
        addUpdateByPrimaryKeyWithBLOBsMethod(interfaze);
        addUpdateByPrimaryKeyWithoutBLOBsMethod(interfaze);
        //
    }
```

## IntrospectedTableMyBatis3SimpleImpl

```java
    protected AbstractJavaClientGenerator createJavaClientGenerator() {
        if (context.getJavaClientGeneratorConfiguration() == null) {
            return null;
        }
        
        String type = context.getJavaClientGeneratorConfiguration()
                .getConfigurationType();

        AbstractJavaClientGenerator javaGenerator;
        if ("XMLMAPPER".equalsIgnoreCase(type)) { //$NON-NLS-1$
            javaGenerator = new SimpleJavaClientGenerator(getClientProject());
        } else if ("ANNOTATEDMAPPER".equalsIgnoreCase(type)) { //$NON-NLS-1$
            javaGenerator = new SimpleAnnotatedClientGenerator(getClientProject());
        } else if ("MAPPER".equalsIgnoreCase(type)) { //$NON-NLS-1$
            javaGenerator = new SimpleJavaClientGenerator(getClientProject());
        } else {
            javaGenerator = (AbstractJavaClientGenerator) ObjectFactory
                    .createInternalObject(type);
        }

        return javaGenerator;
    }
```
打开其中一个生成器，比如SimpleJavaClientGenerator
```java
    @Override
    public List<CompilationUnit> getCompilationUnits() {
        //
        addDeleteByPrimaryKeyMethod(interfaze);
        addInsertMethod(interfaze);
        addSelectByPrimaryKeyMethod(interfaze);
        addSelectAllMethod(interfaze);
        addUpdateByPrimaryKeyMethod(interfaze);
        //
    }
```

至此，找到xxxSelective方法没有生成的原因。
