import argparse
from .tools.assemble import assemble
from .tools.parser import parse_string, parse_template
from .tools.db import save_template


def main():

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="subparser_name")

    assemble_parser = subparsers.add_parser("assemble")
    assemble_parser.add_argument("template")
    assemble_parser.add_argument("--multiprocessing", action="store_true")
    assemble_parser.add_argument("--distributed", action="store_true")
    assemble_parser.add_argument("--host", default="localhost")
    assemble_parser.add_argument("--user", default="guest")
    assemble_parser.add_argument("--password", default="guest")
    assemble_parser.add_argument("kwargs", nargs="*")

    save_parser = subparsers.add_parser("save")
    save_parser.add_argument("filename")

    args = parser.parse_args()
    if args.subparser_name == "assemble":
        template = args.template
        fields = {}
        kwargs = args.kwargs

        if len(kwargs) > 0:
            for kwarg in kwargs:
                field, value = kwarg.split("=")
                fields[field] = value

        assemble(template, template, __name__,
                 multiprocessing=args.multiprocessing,
                 distributed=args.distributed, host=args.host, user=args.user,
                 password=args.password, **fields)
        while True:
            pass

    elif args.subparser_name == "save":
        filename = args.filename
        with open(filename) as f:
            data = f.read()
            templates = parse_string(data)
            for template in templates:
                save_template(parse_template(template))


if __name__ == "__main__":
    main()
