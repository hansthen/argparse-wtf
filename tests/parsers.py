import configargparse


def get_parser_1():
    parser = configargparse.Parser()
    parser.add_argument("--foo", nargs="?", help="foo help")
    parser.add_argument("--bar", nargs="+", help="bar help")
    parser.add_argument("--baz", help="bar help", choices=["1", "2", "3"])
    return parser
