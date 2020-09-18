from pathlib import Path
from typing import Callable, ClassVar, Dict, List, Union
from warnings import warn

from dateutil.parser import parse as parse_datetime

class VcdSyntaxError(Exception):
    pass

END = '$end'

class VCD:
    KEYWORD_PARSERS: ClassVar[Dict[str, Callable[['VCD'], None]]]

    def __init__(self, file: Union[Path, str]) -> None:
        self._file = Path(file)
        self._token_stream = VCD._tokenize(self._file)
        self._current_scope_type = None  # Change to stacks to allow nested scopes
        self._current_scope = None       # (I'm not sure if nested scopes are part of the VCD spec.)
        self._headers_complete = False  # A flag to indicate that all headers have been parsed

        self.comments = []
        self.date = None
        self.version = None
        self.vars = {}

        while not self._headers_complete:
            token = next(self._token_stream)
            self.KEYWORD_PARSERS[token](self)
        self._parse_value_changes()

    @staticmethod
    def _tokenize(file: Path):
        for line in file.open():
            for token in line.split():
                yield token

    def _get_inner_tokens(self) -> List[str]:
        """Retrieves inner tokens of a section and consumes the closing $end token."""
        tokens = []
        for token in self._token_stream:
            if token != END:
                tokens.append(token)
            else:
                break
        return tokens

    def _parse_text(self) -> str:
        """Joins all tokens into a single string using spaces until an $end token is found."""
        tokens = self._get_inner_tokens()
        text = ' '.join(tokens)
        return text

    def _parse_comment(self):
        comment = self._parse_text()
        self.comments.append(comment)

    def _parse_date(self):
        date = self._parse_text()
        try:
            self.date = parse_datetime(date)
        except:
            self.date = date

    def _parse_version(self):
        self.version = self._parse_text()

    def _parse_timescale(self):
        tokens = self._get_inner_tokens()
        if len(tokens) != 2:
            raise VcdSyntaxError('The $timescale section should contain exactly two tokens. ' +
                                 f"Expected '<time_number> <time_unit>' but found {tokens}.")

        UNIT_MULTIPLIERS = dict(s=1.0, ms=1e-3, us=1e-6, ns=1e-9, ps=1e-12, fs=1e-15)
        value = int(tokens[0])
        unit = tokens[1]
        if value not in [1, 10, 100] or unit not in UNIT_MULTIPLIERS:
            raise VcdSyntaxError(f"Timescale value must be 1, 10 or 100. Was {value}." +
                                 f"The unit must be s, ms, us, ns, ps or fs. Was '{unit}'.")
        self.timescale = value*UNIT_MULTIPLIERS[unit]

    def _parse_scope(self):
        tokens = self._get_inner_tokens()
        if len(tokens) != 2:
            raise VcdSyntaxError('The $scope section should contain exactly two tokens. ' +
                                 f"Expected '<scope_type> <identifier>' but found {tokens}.")

        SCOPE_TYPES = ['begin', 'fork', 'function', 'module', 'task']
        if tokens[0] not in SCOPE_TYPES:
            warn(f"Unknown scope type '{tokens[0]}'. Should be one of: {SCOPE_TYPES}")
        self._current_scope_type = tokens[0]  # Push onto a stack to allow nested scopes
        self._current_scope = tokens[1]

    def _parse_upscope(self):
        token = next(self._token_stream)
        if token != END:
            raise VcdSyntaxError(f"Non-empty $upscope section. Found '{token}' after '$upscope'")
        self._current_scope_type = None  # Pop from a stack to allow nested scopes
        self._current_scope = None

    def _parse_var(self):
        tokens = self._get_inner_tokens()
        if len(tokens) != 4:
            raise VcdSyntaxError('The $scope section should contain exactly four tokens. ' +
                    f"Expected '<var_type> <size> <identifier> <reference>' but found {tokens}.")

        VAR_TYPES = ['event', 'integer', 'parameter', 'real', 'reg', 'supply0', 'supply1', 'time',
                     'tri', 'triand', 'trior', 'trireg', 'tri0', 'tri1', 'wand', 'wire', 'wor']
        if tokens[0] not in VAR_TYPES:
            warn(f"Unknown variable type '{tokens[0]}'. Should be one of: {VAR_TYPES}")
        self.vars[tokens[2]] = dict(scope_type=self._current_scope_type,
                                    scope=self._current_scope,
                                    type=tokens[0],
                                    size=int(tokens[1]),
                                    id=tokens[2],
                                    name=tokens[3],
                                    vals=[], timestamps=[])

    def _parse_enddefinitions(self):
        token = next(self._token_stream)
        if token != END:
            raise VcdSyntaxError(
                    f"Non-empty $enddefinitions section. Found '{token}' after '$enddefinitions'")
        self._headers_complete = True

    def _parse_value_changes(self):
        current_timestamp = None
        for token in self._token_stream:
            if token.startswith('#'):
                current_timestamp = int(token[1:])
            else:
                value, var_id = int(token[0]), token[1]  # Assuming all vars are single bit for now
                self.vars[var_id]['vals'].append(value)
                self.vars[var_id]['timestamps'].append(current_timestamp)

VCD.KEYWORD_PARSERS = {
    '$comment':        VCD._parse_comment,
    '$date':           VCD._parse_date,
    '$enddefinitions': VCD._parse_enddefinitions,
    '$scope':          VCD._parse_scope,
    '$timescale':      VCD._parse_timescale,
    '$upscope':        VCD._parse_upscope,
    '$var':            VCD._parse_var,
    '$version':        VCD._parse_version,
}
