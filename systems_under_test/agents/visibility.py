"""security/visibility.py - copied verbatim from Project 7/Project 6's
real, already-proven Accumulo-style visibility parser/evaluator."""
import re
from dataclasses import dataclass


class VisibilityParseError(ValueError):
    pass


@dataclass
class Node:
    op: str
    label: str = None
    children: list = None


_LABEL_PATTERN = re.compile(r"^[A-Za-z0-9_\-]+$")


def _tokenize(expr):
    tokens = []
    current_label = ""
    for ch in expr:
        if ch in "&|()":
            if current_label:
                tokens.append(current_label)
                current_label = ""
            tokens.append(ch)
        elif ch.isspace():
            if current_label:
                tokens.append(current_label)
                current_label = ""
        else:
            current_label += ch
    if current_label:
        tokens.append(current_label)
    return tokens


def parse_visibility(expr):
    expr = expr.strip()
    if not expr:
        raise VisibilityParseError("Empty visibility expression")

    tokens = _tokenize(expr)
    pos = [0]

    def peek():
        return tokens[pos[0]] if pos[0] < len(tokens) else None

    def consume():
        tok = tokens[pos[0]]
        pos[0] += 1
        return tok

    def parse_term():
        tok = peek()
        if tok is None:
            raise VisibilityParseError("Unexpected end of expression")
        if tok == "(":
            consume()
            node = parse_expression()
            if peek() != ")":
                raise VisibilityParseError(f"Expected ')' in: {expr}")
            consume()
            return node
        if tok in ("&", "|", ")"):
            raise VisibilityParseError(f"Unexpected token '{tok}' in: {expr}")
        if not _LABEL_PATTERN.match(tok):
            raise VisibilityParseError(f"Invalid label '{tok}' in: {expr}")
        consume()
        return Node(op="LABEL", label=tok)

    def parse_expression():
        left = parse_term()
        op_seen = None
        children = [left]

        while peek() in ("&", "|"):
            op_tok = consume()
            op = "AND" if op_tok == "&" else "OR"
            if op_seen is not None and op != op_seen:
                raise VisibilityParseError(
                    f"Mixed '&' and '|' without parentheses in: {expr}"
                )
            op_seen = op
            children.append(parse_term())

        if len(children) == 1:
            return children[0]
        return Node(op=op_seen, children=children)

    result = parse_expression()
    if pos[0] != len(tokens):
        raise VisibilityParseError(f"Unexpected trailing tokens in: {expr}")
    return result


def evaluate_visibility(expr, user_authorizations):
    tree = parse_visibility(expr)

    def eval_node(node):
        if node.op == "LABEL":
            return node.label in user_authorizations
        elif node.op == "AND":
            return all(eval_node(child) for child in node.children)
        elif node.op == "OR":
            return any(eval_node(child) for child in node.children)
        raise VisibilityParseError(f"Unknown node op: {node.op}")

    return eval_node(tree)
