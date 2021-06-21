from tests import parsers
import argparse
from wtforms import *
from flask_wtf import FlaskForm
from frozendict import frozendict

import os
from flask import Flask, render_template

app = Flask(__name__)
SECRET_KEY = os.urandom(32)
app.config["SECRET_KEY"] = SECRET_KEY


class Parser:
    def __init__(self, parser, action_registry=None, type_registry=None):
        self.parser = parser
        """
        self.action_registry = action_registry or frozendict()
        self.type_registry = type_registry or frozendict()
        """

    def __str__(self):
        return "parser: " + parser.prog

    def groups(self):
        for group in self.parser._action_groups:
            yield Group(group)

    def create_form(self):
        outer = self

        class F(FlaskForm):
            def validate(self):
                if super().validate():
                    args = self.create_argparse()
                    app.logger.debug("args = %s", args)
                    outer.parser.parse_args(args)
                    return True
                else:
                    return False

            def create_argparse(self):
                args = []
                for name, value in self._create_argparse():
                    args.append("--" + name)
                    if isinstance(value, list):
                        args.extend(value)
                    else:
                        args.append(value)
                return args

            def _create_argparse(self):
                data = self.data
                for name, value in data.items():
                    if name == "positional arguments":
                        continue
                    else:
                        if isinstance(value, dict):
                            yield from value.items()
                        else:
                            continue

        for group in self.groups():
            formfield = FormField(group.create_form())
            setattr(F, group.group.title, formfield)

        return F


class Group:
    def __init__(self, group):
        self.group = group

    def actions(self):
        for action in self.group._group_actions:
            yield Action(action)

    def create_form(self):
        class F(Form):
            pass

        for action in self.actions():
            field = action.create_field()
            if field:
                setattr(F, action.action.metavar or action.action.dest, field)
        return F

    def __str__(self):
        return "--" + self.group.title + "--"


class Action:
    def __init__(self, action):
        self.action = action

    def create_field(self):
        if isinstance(self.action, argparse._HelpAction):
            return None
        if isinstance(self.action, argparse._VersionAction):
            return HiddenField(self.action.metavar or self.action.dest)
        if isinstance(self.action, argparse._StoreConstAction):
            return BooleanField(self.action.metavar or self.action.dest)
        elif self.action.choices:
            return SelectField(
                self.action.metavar or self.action.dest, choices=self.action.choices
            )
        elif self.action.nargs in ("+", "*"):
            return FieldList(
                StringField(self.action.metavar or self.action.dest),
                min_entries=2,
                max_entries=4,
            )
        else:
            return StringField(self.action.metavar or self.action.dest)

    def __str__(self):
        return "%s : %s [%s]" % (
            self.action.metavar or self.action.dest,
            self.action.type,
            self.action.nargs,
        )


def _parse_from_argparse(parser):
    yield Parser(parser)
    for group in parser._action_groups:
        yield Group(group)
        for action in group._group_actions:
            yield Action(action)


@app.route("/", methods=["GET", "POST"])
def index():
    parser = parsers.get_parser_1()
    p = Parser(parser)
    F = p.create_form()
    my_form = F()
    if not my_form.validate():
        return render_template("index.html", form=my_form)
    else:
        return "Ok"
