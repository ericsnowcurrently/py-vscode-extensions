import re


def iter_lines(lines):
    """Yield every significant line."""
    commented = False
    for line in lines:
        line = line.strip()
        # Ignore blank lines.
        if not line:
            continue
        # Ignore comments.
        if line.endswith('*/'):
            commented = False
            continue
        elif commented:
            continue
        if line.startswith('/*'):
            commented = True
            continue
        elif line.startswith('//'):
            continue

        yield line


_COMPOUND = {
        'module': ('namespace', 'interface', 'class', 'enum', None),
        'namespace': ('namespace', 'interface', 'class', 'enum', None),
        'interface': ('inline', None),
        'class': ('inline', None),
        'type': ('inline', None),
        'inline': ('inline', None),
        'enum': (None,),
        }

def parse_declarations(lines, *,
                       _iter_lines=iter_lines,
                       ):
    """Return the VS Code API defined in the given text of vscode.d.ts."""
    if isinstance(lines, str):
        lines = lines.splitlines()
    lines = _iter_lines(lines)

    api = {}
    parent = api
    allowed = ('module', 'namespace', 'interface', 'class')
    parents = [(parent, allowed)]
    for line in lines:
        # Handle exiting a block.
        if line == '}[];':
            parent['_isarray'] = True;
            line = '}'
        if line == '}' or line == '};':
            parents.pop()
            if not parents:
                raise ValueError('unexpected closing bracket')
            parent, allowed = parents[-1]
            continue

        # Parse the next line.
        name, kind = _parse_line(line)
        if kind not in allowed:
            raise ValueError('unsupported line {!r}'.format(line))

        # Handle methods and properties.
        if not kind:
            if not name:
                if parent['_kind'] != 'interface':
                    raise ValueError('unexpected line {!r}'.format(line))
                name = '<function>'
            try:
                prop = parent[name]
            except KeyError:
                prop = parent[name] = []
            prop.append(line)
            continue

        # Enter the new parent.
        compound = {
                '_raw': line,
                '_kind': kind,
                }
        if name in parent:
            raise ValueError('duplicate name in {!r}'.format(line))
        parent[name] = compound
        try:
            parent, allowed = compound, _COMPOUND[kind]
        except KeyError:
            raise ValueError('unsupported kind in {!r}'.format(line))
        parents.append((parent, allowed))

    return api


COMPOUND_RE = re.compile(r'''
        (?:
          declare \s+ module \s+ '(?P<module>\w+)' \s* {
          ) |
        (?: export \s+ )?
        (?:
          (?:
            namespace \s+ (?P<namespace>\w+) \s* {
            ) |
          (?:
            interface \s+ (?P<interface>\w+)
            (?: \s* [<] (?: \s* \S+ )+ \s* [>] \s* | \s+ )
            (?: extends \s+ \w+ )?
            \s* {
            ) |
          (?:
            class \s+ (?P<class>\w+)
            (?: \s* [<] (?: \s* \S+ )+ \s* [>] )?
            (?: \s+ extends \s+ \w+ )?
            (?: \s+ implements \s+ \w+ )?
            \s* {
            ) |
          (?:
            type \s+ (?P<type>\w+) \s* = {
            ) |
          (?:
            (?P<inline>\w+) \s*
            (?: [?] \s* )?
            : .* { $
            #: (?: \s* \S+ )? \s* { $
            ) |
          (?:
            enum \s+ (?P<enum>\w+) \s* {
            )
          )
        ''', re.VERBOSE)
# XXX fix "types" (trailing text)
SIMPLE_RE = re.compile(r'''
        (?:
          # types
          (?: export \s+ )?
          type \s+ (\w+)
          (?: \s* [<] (?: \s* \S+ )+ \s* [>] )?
          #\s* = (?: \s* \S+ )+ \s* ;
          ) |
        (?:
          # constructors
          (?: protected \s+ )?
          (?: private \s+ )?
          ( constructor ) \s* [(] .* [)] \s* ;?
          ) |
        (?:
          # methods / functions
          (?: export \s+ )?
          (?: static \s+ )?
          (?: function \s+ )?
          ( \w+ ) \s*
          (?: [?] \s* )?
          (?: [<] .* [>] \s* )?
          #(?: [<] (?: \s* \S+ )+ \s* [>] \s* )?
          [(] .* [)] \s* : \s* .* \s* ;
          ) |
        (?:
          # properties
          (?: export \s+ )?
          (?: static \s+ )?
          (?: const \s+ )?
          (?: readonly \s+ )?
          (?: let \s+ )?
          ( \w+ ) \s*
          (?:
            [?]? \s* :
            |
            =
            )
          (?: \s* \S+ )+ \s* ;
          ) |
        (?:
          # enum items
          ( \w+ ) \s* = \s* \S+ \s* ,?
          ) |
        (?:
          # interface-as-mapping
          (?: readonly \s+ )?
          [[] \s* [^]]+ \s* []] \s* : (?: \s* \S+ )* \s* ;
          ) |
        (?:
          # function sig as interface
          [(] .* [)] \s* : (?: \s* \S+ )* \s* ;
          )
        ''', re.VERBOSE)


def _parse_line(line):
    m = COMPOUND_RE.match(line)
    if m:
        for kind, name in m.groupdict().items():
            if name:
                return name, kind
        else:
            raise ValueError('unexpected line {!r}'.format(line))

    m = SIMPLE_RE.match(line)
    if not m:
        raise ValueError('unsupported line {!r}'.format(line))
    for name in m.groups():
        if name:
            if name == 'constructor':
                name = '<constructor>'
            return name, None
    else:
        # function sig as interface
        return None, None
        #raise ValueError('unexpected line {!r}'.format(line))
