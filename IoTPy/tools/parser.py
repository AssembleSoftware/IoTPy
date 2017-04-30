from pyparsing import *
from .db import get_template
from .parameter import get_external, make_internal, Parameter

# Literals
lineEnd = Suppress(Literal(";"))

leftBracket = Suppress(Literal("["))
rightBracket = Suppress(Literal("]"))

leftBrace = Suppress(Literal("{"))
rightBrace = Suppress(Literal("}"))

leftParan = Suppress(Literal("("))
rightParan = Suppress(Literal(")"))

equals = Suppress(Literal("="))
arrow = Suppress(Literal("->"))

# Common

# Template name
name = Word(alphanums + "_").setResultsName("name")

# Field name
field = Word(alphas + "_")

# Optional field
optional_field = Combine(field + Literal("*"))

# Typed field
typed_field = Group((field ^ optional_field) + Suppress(Literal(":")) +
                    Word(alphas))

# Declaration

# List of fields
inputs = Group(leftParan +
               Optional(delimitedList(field ^ optional_field ^ typed_field)) +
               rightParan).setResultsName("inputs")

# List of outputs
outputs = Group(delimitedList(field ^ typed_field)).setResultsName("outputs")

# Statement

# Output
# Either a field or a list of fields enclosed in []
# If only one field is provided, return as a list
param = field | Group(leftBracket + delimitedList(field) + rightBracket)

# Keyword value
val = Word(alphanums + "._") | Combine(
    Literal("\"") + Word(alphanums + "._") + Literal("\""))

val1 = val | leftBracket + Group(delimitedList(val)) + rightBracket

# Field keyword
fieldKeyword = Group(field + equals + val1)

inputsLine = Group(leftParan + Optional(delimitedList(fieldKeyword)) +
                   rightParan).setResultsName("inputs")

# Inputs

# Outputs
outputsLine = Group(delimitedList(param)).setResultsName("outputs")

# Parser

first = name + inputs + arrow + outputs
line = Optional(outputsLine + equals) + name + inputsLine + lineEnd
lines = ZeroOrMore(Group(line)).setResultsName("lines")

template = first + leftBrace + lines + rightBrace
templates = OneOrMore(Group(template))


def parse_string(x):
    """ Parses a string using the parser

    Parameters
    ----------
    x : str
        String that describes template

    Returns
    -------
    pyparsing.ParseResults

    """
    return templates.parseString(x)


def get_templates(x):
    """ Parses a string containing templates to dict 

    Parameters
    ----------
    x : str
        String that describes templates

    Returns
    -------
    list
        List containing dict for templates

    """
    templates = parse_string(x)
    y = []
    for template in templates:
        y.append(parse_template(template))

    return y


def parse_template(template):
    """ Creates a dict for a template

    Parameters
    ----------
    template : pyparsing.ParseResults
        Template parsed using parser

    Returns
    -------
    dict
        Dict for template

    """
    args_dict = {}

    # Get name of template
    args_dict["name"] = template["name"]

    # Parse inputs
    args_dict["inputs"] = []
    args_dict["optional"] = []
    if "inputs" in template:
        for field in template["inputs"]:
            # Typed field
            try:

                field_name, field_type = field.asList()

                # Optional
                if field_name[-1] == "*":
                    args_dict["optional"].append([field_name[0:-1]])
                    args_dict["inputs"].append([field_type, field_name[0:-1]])
                else:
                    args_dict["inputs"].append([field_type, field_name])

            except BaseException:
                # Optional
                if field[-1] == "*":
                    args_dict["optional"].append(field[0:-1])
                    args_dict["inputs"].append(field[0:-1])
                else:
                    args_dict["inputs"].append(field)

    # Parse outputs
    args_dict["outputs"] = []
    output_names = []
    if "outputs" in template:
        for field in template["outputs"]:
            # Typed field
            try:
                field_name, field_type = field.asList()
                args_dict["outputs"].append([field_type, field_name])
                output_names.append(field_name)

            except BaseException:

                # No return val
                if field == "None":
                    continue
                args_dict["outputs"].append(field)
                output_names.append(field)

    # Subparts
    if "lines" in template:
        args_dict["assembly"] = "assemble"
        args_dict["components"] = []
        args_dict["externals"] = []
        args_dict["internals"] = []
        outputs = {}

        # Dict of subpart ids
        template_count = {}
        for line in template["lines"]:
            name = line["name"]
            if name in template_count:
                template_count[name] += 1
            else:
                template_count[name] = 0

            # Create name for subpart using id
            name_subpart = name + str(template_count[name])

            args_dict["components"].append([name_subpart, name])

            # Read template from db
            y = get_template(name)

            # Parse outputs of line
            if "outputs" in line:

                # Outputs from line
                line_outputs = line["outputs"].asList()

                # Outputs of template
                template_outputs = y["outputs"]

                # Iterate over each list of outputs
                for i in range(0, len(line_outputs)):
                    # Iterate over each output
                    output = template_outputs[i]

                    # output = type, name
                    if isinstance(output, list):
                        output = output[1]

                    # Single output
                    if not isinstance(line_outputs[i], list):

                        # External
                        if line_outputs[i] in output_names:
                            args_dict["externals"].append(
                                [line_outputs[i], name_subpart, output])
                        # Temporary var
                        else:
                            outputs[line_outputs[i]] = [name_subpart, output]

                    # List of outputs
                    else:
                        for j in range(0, len(line_outputs[i])):

                            # External connection
                            if line_outputs[i][j] in output_names:
                                args_dict["externals"].append([
                                    line_outputs[i][j], name_subpart, output, j
                                ])

                            # Temporary var
                            else:
                                outputs[line_outputs[i][j]] = [
                                    name_subpart, output, j
                                ]

        # Dict of temp variable count
        output_counts = {}

        # Dict of subpart ids
        template_count = {}
        for line in template["lines"]:
            name = line["name"]
            if name in template_count:
                template_count[name] += 1
            else:
                template_count[name] = 0

            # Create name for subpart wth id
            name_subpart = name + str(template_count[name])
            y = get_template(name)

            # Parse inputs of line
            if "inputs" in line:

                # Inputs from line
                inputs = line["inputs"].asList()

                # Iterate over each list of inputs
                for key, value in inputs:

                    # Single input
                    if not isinstance(value, list):
                        # Temporary var
                        if value in outputs:
                            if value in output_counts:
                                output_counts[value] += 1
                            else:
                                output_counts[value] = 1

                            source = get_external(outputs[value])
                            des = Parameter(name_subpart, key, None)
                            args_dict["internals"].append(
                                make_internal(source, des))

                        # External connection
                        else:
                            args_dict["externals"].append(
                                [value, name_subpart, key])

                    # List of inputs
                    else:
                        # Iterate over each stream
                        for j in range(0, len(value)):

                            # Temporary var
                            if value[j] in outputs:

                                if value[j] in output_counts:
                                    output_counts[value[j]] += 1
                                else:
                                    output_counts[value[j]] = 1
                                source = get_external(outputs[value[j]])
                                des = Parameter(name_subpart, key, j)
                                args_dict["internals"].append(
                                    make_internal(source, des))

                            # External connection
                            else:
                                args_dict["externals"].append(
                                    [value[j], name_subpart, key, j])

        for value in outputs:
            if value not in output_counts:
                args_dict["externals"].append(["None"] + outputs[value])


    # No lines
    else:
        args_dict["assembly"] = template["name"]
    return args_dict
