---
layout: default
title: Skydoc Deprecation
stylesheet: docs
---

## Why was Skydoc deprecated?

Skydoc functioned by evalutating Starlark files as if they were python. Unfortunately, while
Starlark is **similar** to Python, there are some important syntactic differences between
the languages. Assuming compatibility between the languages was inherently brittle, and resulted
in a maintenance burden on the Starlark code. Specifically, if one of your transitive dependencies
were to adopt a Starlark-compatible, python-incompatible construct, your Skydoc integration would
break!

Skydoc still exists as it's a nontrivial migration to Stardoc, but we plan on removing it
in mid 2019.

## How to migrate

Stardoc is not a drop-in replacement for Skydoc. Its usage is slightly different, and it has some
new features. It's recommended to take a look at the root Stardoc documentation, but here is
a brief summary of some things to note for migration:

### Docstring specification

Stardoc uses inline documentation strings instead of python-style docstrings.
For example, Skydoc documentation may have been specified with:

```
my_rule = rule(
    implementation = _my_rule_impl,
    attrs = {
        "srcs": attr.label_list(),
        "deps": attr.label_list(),
    },
)
"""Example rule documentation.

Example:
  Here is an example of how to use this rule.

Args:
  srcs: Source files used to build this target.
  deps: Dependencies for this target.
"""
```

...the equivalent for Stardoc is:

```
my_rule = rule(
    implementation = _my_rule_impl,
    doc = """
Example rule documentation.

Example:
  Here is an example of how to use this rule.
""",
    attrs = {
        "srcs" : attr.label_list(
            doc = "Source files used to build this target.",
        ),
        "deps" : attr.label_list(
            doc = "Dependencies for this target.",
        ),
    }
)
```

### Different Starlark Rule

Stardoc uses a different Starlark rule than Skydoc with different attributes.

See [Generating Documentation](https://skydoc.bazel.build/docs/generating_stardoc.html) for a
tutorial on using the new rule, and the
[Build Rule Reference](https://skydoc.bazel.build/docs/stardoc_reference.html) for information
about the new `stardoc` rule itself.

### Starlark Dependencies

Stardoc depends on your `bzl` file, all of its dependencies, and all of its **transitive**
dependencies, so that it can fully evaluate your Starlark code.
`bazel-skylib`'s `bzl_library` is your "best friend" for tracking `bzl` dependencies.

For example, suppose your `mypackage/foo.bzl` file depends on `other/package/bar.bzl`, which
depends on `third/package/baz.bzl`.

**BUILD**:

```
load("@io_bazel_skydoc//stardoc:stardoc.bzl", "stardoc")

stardoc(
    name = "foo_docs",
    input = "foo.bzl",
    out = "foo_doc.md",
    deps = ["//other/package:bar"],
)
```

**other/package/BUILD**:

```
load("@bazel_skylib//:bzl_library.bzl", "bzl_library")

bzl_library(
    name = "bar",
    srcs = ["bar.bzl"],
    deps = ["//third/package:baz"],
)
```

**third/package/BUILD**:

```
load("@bazel_skylib//:bzl_library.bzl", "bzl_library")

bzl_library(
    name = "baz",
    srcs = ["baz.bzl"],
)
```

Thus, each `.bzl` file should appear in the `srcs` of a `bzl_library` target defined in the same
package. The `deps` of this `bzl_library` should be (only) the `bzl_library` targets corresponding
to the files that are _directly_ `load()`ed by the `srcs`. This structure mirrors that of other
`<language>_library` rules in Bazel.

This migration might involve creating a large number of new `bzl_library` targets,
but this work is useful beyond Stardoc. For example, `bzl_library` can be also used to gather
transitive Starlark dependencies for use in shell tests or other test frameworks.

See [Generating Documentation](https://skydoc.bazel.build/docs/generating_stardoc.html) for
a tutorial.

## Migration Issues

If you run into any issues migrating, please file a
[github issue](https://github.com/bazelbuild/skydoc/issues).

