from app.parsing.clausewitz import parse, as_list


def test_scalars_and_types():
    tree = parse('a=1\nb=1.5\nc="hi"\nd=yes\ne=no\nf=bareword\n')
    assert tree == {"a": 1, "b": 1.5, "c": "hi", "d": True, "e": False, "f": "bareword"}


def test_nested_dict_block():
    tree = parse("outer={ a=1 b=2 }")
    assert tree == {"outer": {"a": 1, "b": 2}}


def test_scalar_list_block():
    tree = parse("nums={ 1 2 3 }")
    assert tree == {"nums": [1, 2, 3]}


def test_duplicate_keys_become_list_in_order():
    tree = parse('x={a="1"}\nx={a="2"}\nx={a="3"}\n')
    assert tree["x"] == [{"a": "1"}, {"a": "2"}, {"a": "3"}]


def test_as_list_normalizes_single_and_missing():
    assert as_list(None) == []
    assert as_list({"a": 1}) == [{"a": 1}]
    assert as_list([1, 2]) == [1, 2]


def test_comments_are_stripped():
    tree = parse("a=1 # this is a comment\nb=2\n")
    assert tree == {"a": 1, "b": 2}


def test_real_tradenode_snippet():
    snippet = """
    kongo={
        location=4097
        inland=yes
        outgoing={
            name="ivory_coast"
            path={ 1170 1464 }
        }
        outgoing={
            name="zambezi"
            path={ 4046 1191 }
        }
        members={ 798 1169 1170 }
    }
    """
    tree = parse(snippet)
    kongo = tree["kongo"]
    assert kongo["location"] == 4097
    assert kongo["inland"] is True
    outgoing = as_list(kongo["outgoing"])
    assert [o["name"] for o in outgoing] == ["ivory_coast", "zambezi"]
    assert kongo["members"] == [798, 1169, 1170]
