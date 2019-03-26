# Copyright 2016 The Bazel Authors. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import os
import tempfile
import textwrap
import unittest
# internal imports

from google.protobuf import text_format
from skydoc import build_pb2
from skydoc import load_extractor
from skydoc import rule_extractor


class RuleExtractorTest(unittest.TestCase):

  def test_create_stubs(self):
    stubs = {
        'foo': 'bar',
        'bar': 'baz',
    }
    load_symbols = [
        load_extractor.LoadSymbol('//foo:bar.bzl', 'bar_library', None),
        load_extractor.LoadSymbol('//foo:bar.bzl', 'foo_bar_binary',
                                  'bar_binary'),
    ]
    expected = {
        'foo': 'bar',
        'bar': 'baz',
        'bar_library': '',
        'bar_binary': '',
        }
    self.assertEqual(expected, rule_extractor.create_stubs(stubs, load_symbols))


  def check_protos(self, src, expected, load_symbols=[]):
    tf = tempfile.NamedTemporaryFile(mode='w+', delete=False)
    tf.write(src)
    tf.flush()
    tf.close()

    expected_proto = build_pb2.BuildLanguage()
    text_format.Merge(expected, expected_proto)

    extractor = rule_extractor.RuleDocExtractor()
    extractor.parse_bzl(tf.name, load_symbols)
    os.remove(tf.name)
    proto = extractor.proto()
    self.assertEqual(expected_proto, proto)

  def test_all_types(self):
    src = textwrap.dedent("""\
        def impl(ctx):
          return struct()

        all_types = rule(
            implementation = impl,
            attrs = {
                "arg_bool": attr.bool(default=True),
                "arg_int": attr.int(default=10),
                "arg_int_list": attr.int_list(default=[1, 2]),
                "arg_label": attr.label(
                    default=Label("//foo:bar",
                                  relative_to_caller_repository=True)),
                "arg_label_list": attr.label_list(
                    default=[Label("//foo:bar"), Label("//bar:baz")]),
                "arg_license": attr.license(),
                "arg_output": attr.output(default=Label("//foo:bar")),
                "arg_output_list": attr.output_list(
                    default=[Label("//foo:bar"), Label("//bar:baz")]),
                "arg_string": attr.string(default="foo"),
                "arg_string_dict": attr.string_dict(default={"foo": "bar"}),
                "arg_string_list": attr.string_list(default=["foo", "bar"]),
                "arg_string_list_dict": attr.string_list_dict(
                    default={"foo": ["bar", "baz"]}),
            },
        )
        \"\"\"Test rule with all types.

        Args:
          name: A unique name for this rule.
          arg_bool: A boolean argument.
          arg_int: An integer argument.
          arg_int_list: A list of integers argument.
          arg_label: A label argument.
          arg_label_list: A list of labels argument.
          arg_license: A license argument.
          arg_output: An output argument.
          arg_output_list: A list of outputs argument.
          arg_string: A string argument.
          arg_string_dict: A dictionary mapping string to string argument.
          arg_string_list: A list of strings argument.
          arg_string_list_dict: A dictionary mapping string to list of string argument.
        \"\"\"
        """)

    expected = textwrap.dedent("""
        rule {
          name: "all_types"
          documentation: "Test rule with all types."
          attribute {
            name: "name"
            type: UNKNOWN
            mandatory: true
            documentation: "A unique name for this rule."
          }
          attribute {
            name: "arg_bool"
            type: BOOLEAN
            mandatory: false
            documentation: "A boolean argument."
            default: "True"
          }
          attribute {
            name: "arg_int"
            type: INTEGER
            mandatory: false
            documentation: "An integer argument."
            default: "10"
          }
          attribute {
            name: "arg_int_list"
            type: INTEGER_LIST
            mandatory: false
            documentation: "A list of integers argument."
            default: "[1, 2]"
          }
          attribute {
            name: "arg_label"
            type: LABEL
            mandatory: false
            documentation: "A label argument."
            default: "//foo:bar"
          }
          attribute {
            name: "arg_label_list"
            type: LABEL_LIST
            mandatory: false
            documentation: "A list of labels argument."
            default: "[\'//foo:bar\', \'//bar:baz\']"
          }
          attribute {
            name: "arg_license"
            type: LICENSE
            mandatory: false
            documentation: "A license argument."
          }
          attribute {
            name: "arg_output"
            type: OUTPUT
            mandatory: false
            documentation: "An output argument."
            default: "//foo:bar"
          }
          attribute {
            name: "arg_output_list"
            type: OUTPUT_LIST
            mandatory: false
            documentation: "A list of outputs argument."
            default: "[\'//foo:bar\', \'//bar:baz\']"
          }
          attribute {
            name: "arg_string"
            type: STRING
            mandatory: false
            documentation: "A string argument."
            default: "\'foo\'"
          }
          attribute {
            name: "arg_string_dict"
            type: STRING_DICT
            mandatory: false
            documentation: "A dictionary mapping string to string argument."
            default: "{\'foo\': \'bar\'}"
          }
          attribute {
            name: "arg_string_list"
            type: STRING_LIST
            mandatory: false
            documentation: "A list of strings argument."
            default: "[\'foo\', \'bar\']"
          }
          attribute {
            name: "arg_string_list_dict"
            type: STRING_LIST_DICT
            mandatory: false
            documentation: "A dictionary mapping string to list of string argument."
            default: "{\'foo\': [\'bar\', \'baz\']}"
          }
          type: RULE
        }
        """)

    self.check_protos(src, expected)

  def test_undocumented(self):
    src = textwrap.dedent("""\
        def _impl(ctx):
          return struct()

        undocumented = rule(
            implementation = _impl,
            attrs = {
                "arg_label": attr.label(),
                "arg_string": attr.string(),
            },
        )
        """)

    expected = textwrap.dedent("""\
        rule {
          name: "undocumented"
          attribute {
            name: "name"
            type: UNKNOWN
            mandatory: true
          }
          attribute {
            name: "arg_label"
            type: LABEL
            mandatory: false
          }
          attribute {
            name: "arg_string"
            type: STRING
            mandatory: false
            default: "''"
          }
          type: RULE
        }
        """)

    self.check_protos(src, expected)

  def test_private_rules_skipped(self):
    src = textwrap.dedent("""\
        def _private_impl(ctx):
          return struct()

        def _public_impl(ctx):
          return struct()

        _private = rule(
            implementation = _private_impl,
            attrs = {
                "arg_label": attr.label(),
                "arg_string": attr.string(),
            },
        )
        \"\"\"A private rule that should not appear in documentation.

        Args:
          name: A unique name for this rule.
          arg_label: A label argument.
          arg_string: A string argument.
        \"\"\"

        public = rule(
            implementation = _public_impl,
            attrs = {
                "arg_label": attr.label(),
                "arg_string": attr.string(),
            },
        )
        \"\"\"A public rule that should appear in documentation.

        Args:
          name: A unique name for this rule.
          arg_label: A label argument.
          arg_string: A string argument.
        \"\"\"
        """)

    expected = textwrap.dedent("""
        rule {
          name: "public"
          documentation: "A public rule that should appear in documentation."
          attribute {
            name: "name"
            type: UNKNOWN
            mandatory: true
            documentation: "A unique name for this rule."
          }
          attribute {
            name: "arg_label"
            type: LABEL
            mandatory: false
            documentation: "A label argument."
          }
          attribute {
            name: "arg_string"
            type: STRING
            mandatory: false
            documentation: "A string argument."
            default: "''"
          }
          type: RULE
        }
        """)

    self.check_protos(src, expected)

  def test_rule_with_generated_impl(self):
    src = textwrap.dedent("""\
        def real_impl(ctx):
          return struct()

        def macro():
          return real_impl

        impl = macro()

        thisrule = rule(
            implementation = impl,
        )
        """)

    expected = textwrap.dedent("""\
        rule {
          name: "thisrule"
          attribute {
            name: "name"
            type: UNKNOWN
            mandatory: true
          }
          type: RULE
        }
        """)

    self.check_protos(src, expected)

  def test_multi_line_description(self):
    src = textwrap.dedent("""\
        def _impl(ctx):
          return struct()

        multiline = rule(
            implementation = _impl,
            attrs = {
                "arg_bool": attr.bool(),
                "arg_label": attr.label(),
            },
        )
        \"\"\"A rule with multiline documentation.

        Some more documentation about this rule here.

        Args:
          name: A unique name for this rule.
          arg_bool: A boolean argument.

            Documentation for arg_bool continued here.
          arg_label: A label argument.

            Documentation for arg_label continued here.
        \"\"\"
        """)

    expected = textwrap.dedent("""\
        rule {
          name: "multiline"
          documentation: "A rule with multiline documentation.\\n\\nSome more documentation about this rule here."
          attribute {
            name: "name"
            type: UNKNOWN
            mandatory: true
            documentation: "A unique name for this rule."
          }
          attribute {
            name: "arg_bool"
            type: BOOLEAN
            mandatory: false
            documentation: "A boolean argument.\\n\\nDocumentation for arg_bool continued here."
            default: "False"
          }
          attribute {
            name: "arg_label"
            type: LABEL
            mandatory: false
            documentation: "A label argument.\\n\\nDocumentation for arg_label continued here."
          }
          type: RULE
        }
        """)

    self.check_protos(src, expected)

  def test_rule_macro_mix(self):
    src = textwrap.dedent("""\
        def _impl(ctx):
          return struct()

        example_rule = rule(
            implementation = _impl,
            attrs = {
                "arg_label": attr.label(),
                "arg_string": attr.string(),
            },
        )
        \"\"\"An example rule.

        Args:
          name: A unique name for this rule.
          arg_label: A label argument.
          arg_string: A string argument.
        \"\"\"

        def example_macro(name, foo, visibility=None):
          \"\"\"An example macro.

          Args:
            name: A unique name for this rule.
            foo: A test argument.
            visibility: The visibility of this rule.
          \"\"\"
          native.genrule(
              name = name,
              out = ["foo"],
              cmd = "touch $@",
              visibility = visibility,
          )
        """)

    expected = textwrap.dedent("""\
        rule {
          name: "example_rule"
          documentation: "An example rule."
          attribute {
            name: "name"
            type: UNKNOWN
            mandatory: true
            documentation: "A unique name for this rule."
          }
          attribute {
            name: "arg_label"
            type: LABEL
            mandatory: false
            documentation: "A label argument."
          }
          attribute {
            name: "arg_string"
            type: STRING
            mandatory: false
            documentation: "A string argument."
            default: "''"
          }
          type: RULE
        }
        """)

    self.check_protos(src, expected)

  def test_rule_with_example_doc(self):
    src = textwrap.dedent("""\
        def _impl(ctx):
          return struct()

        rule_with_example = rule(
            implementation = _impl,
            attrs = {
                "arg_label": attr.label(),
                "arg_string": attr.string(),
            },
        )
        \"\"\"Rule with example.

        Example:
          Here is an example of how to use this rule.

        Args:
          name: A unique name for this rule.
          arg_label: A label argument.
          arg_string: A string argument.
        \"\"\"
        """)

    expected = textwrap.dedent("""\
        rule {
          name: "rule_with_example"
          documentation: "Rule with example."
          example_documentation: "Here is an example of how to use this rule."
          attribute {
            name: "name"
            type: UNKNOWN
            mandatory: true
            documentation: "A unique name for this rule."
          }
          attribute {
            name: "arg_label"
            type: LABEL
            mandatory: false
            documentation: "A label argument."
          }
          attribute {
            name: "arg_string"
            type: STRING
            mandatory: false
            documentation: "A string argument."
            default: "''"
          }
          type: RULE
        }
        """)

    self.check_protos(src, expected)

  def test_rule_with_output_doc(self):
    src = textwrap.dedent("""\
        def _impl(ctx):
          return struct()

        rule_with_outputs = rule(
            implementation = _impl,
            attrs = {
                "arg_label": attr.label(),
                "arg_string": attr.string(),
            },
            outputs = {
                "jar": "%{name}.jar",
                "deploy_jar": "%{name}_deploy.jar",
            },
        )
        \"\"\"Rule with output documentation.

        Outputs:
          jar: A Java archive.
          deploy_jar: A Java archive suitable for deployment.

              Only built if explicitly requested.

        Args:
          name: A unique name for this rule.
          arg_label: A label argument.
          arg_string: A string argument.
        \"\"\"
        """)

    expected = textwrap.dedent("""\
        rule {
          name: "rule_with_outputs"
          documentation: "Rule with output documentation."
          attribute {
            name: "name"
            type: UNKNOWN
            mandatory: true
            documentation: "A unique name for this rule."
          }
          attribute {
            name: "arg_label"
            type: LABEL
            mandatory: false
            documentation: "A label argument."
          }
          attribute {
            name: "arg_string"
            type: STRING
            mandatory: false
            documentation: "A string argument."
            default: "''"
          }
          output {
            template: "%{name}.jar"
            documentation: "A Java archive."
          }
          output {
            template: "%{name}_deploy.jar"
            documentation: "A Java archive suitable for deployment.\\n\\nOnly built if explicitly requested."
          }
          type: RULE
        }
        """)

    self.check_protos(src, expected)

  def test_loads(self):
    src = textwrap.dedent("""\
        load("//foo/bar:bar.bzl", "foo_library")
        load("//foo/bar:baz.bzl", "foo_test", orig_foo_binary = "foo_binary")

        _references_foo_library = foo_library
        _references_orig_foo_binary = orig_foo_binary
        """)
    load_symbols = [
        load_extractor.LoadSymbol('//foo/bar:bar.bzl', 'foo_library', None),
        load_extractor.LoadSymbol('//foo/bar:baz.bzl', 'foo_test', None),
        load_extractor.LoadSymbol('//foo/bar:baz.bzl', 'foo_binary',
                                  'orig_foo_binary'),
    ]
    expected = ""
    self.check_protos(src, expected, load_symbols)

  def test_repository_rule(self):
    src = textwrap.dedent("""\
        def _impl(repository_ctx):
          return struct()

        repo_rule = repository_rule(
            implementation = _impl,
            local = True,
            attrs = {
                "path": attr.string(mandatory=True)
            },
        )
        \"\"\"A repository rule.

        Args:
          name: A unique name for this rule.
          path: The path of the external dependency.
        \"\"\"
        """)

    expected = textwrap.dedent("""\
        rule {
          name: "repo_rule"
          documentation: "A repository rule."
          attribute {
            name: "name"
            type: UNKNOWN
            mandatory: true
            documentation: "A unique name for this rule."
          }
          attribute {
            name: "path"
            type: STRING
            mandatory: true
            documentation: "The path of the external dependency."
            default: "\'\'"
          }
          type: REPOSITORY_RULE
        }
        """)

    self.check_protos(src, expected)

  def test_doc_arg(self):
    src = textwrap.dedent("""\
        def _impl(ctx):
          return struct()

        rule_with_doc = rule(
            implementation = _impl,
            attrs = {
                "foo": attr.string(doc = "Attribute documentation.")
            },
        )
        \"\"\"A rule.
        \"\"\"
        """)

    expected = textwrap.dedent("""\
        rule {
          name: "rule_with_doc"
          documentation: "A rule."
          attribute {
            name: "name"
            type: UNKNOWN
            mandatory: true
          }
          attribute {
            name: "foo"
            type: STRING
            mandatory: false
            documentation: "Attribute documentation."
            default: "\'\'"
          }
          type: RULE
        }
        """)

    self.check_protos(src, expected)

if __name__ == '__main__':
  unittest.main()
