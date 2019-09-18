# This is based on the pep508-parser grammer at https://github.com/NFJones/pep508-parser
# MIT Licensed
"""
Requirements parsing functions
"""
import logging
import os
import platform
import sys
from typing import Dict

import distro
import parsley
import pkg_resources


logger = logging.getLogger(__name__)


GRAMMAR: str = """
    wsp            = ' ' | '\t'
    version_cmp    = wsp* <'<=' | '<' | '!=' | '==' | '>=' | '>' | '~=' | '==='>
    version        = wsp* <( letterOrDigit | '-' | '_' | '.' | '*' | '+' | '!' )+>
    version_one    = version_cmp:op version:v wsp* -> (op, v)
    version_many   = version_one:v1 (wsp* ',' version_one)*:v2 -> [v1] + v2
    versionspec    = ('(' version_many:v ')' ->v) | version_many
    urlspec        = '@' wsp* <URI_reference>
    marker_op      = version_cmp | (wsp* 'in') | (wsp* 'not' wsp+ 'in')
    python_str_c   = (wsp | letter | digit | '(' | ')' | '.' | '{' | '}' |
                      '-' | '_' | '*' | '#' | ':' | ';' | ',' | '/' | '?' |
                      '[' | ']' | '!' | '~' | '`' | '@' | '$' | '%' | '^' |
                      '&' | '=' | '+' | '|' | '<' | '>' )
    dquote         = '"'
    squote         = '\\''
    python_str     = (squote <(python_str_c | dquote)*>:s squote |
                      dquote <(python_str_c | squote)*>:s dquote) -> s
    env_var        = ('python_version' | 'python_full_version' |
                      'os_name' | 'sys_platform' | 'platform_release' |
                      'platform_system' | 'platform_version' |
                      'platform_machine' | 'platform_python_implementation' |
                      'implementation_name' | 'implementation_version' |
                      'distro_codename' | 'distro_name' | 'distro_id' |
                      'distro_like' | 'distro_version' |
                      'extra' # ONLY when defined by a containing layer
                      ):varname -> lookup(varname)
    marker_var     = wsp* (env_var | python_str)
    marker_expr    = marker_var:l marker_op:o marker_var:r -> (o, l, r)
                   | wsp* '(' marker:m wsp* ')' -> m
    marker_and     = marker_expr:l wsp* 'and' marker_expr:r -> ('and', l, r)
                   | marker_expr:m -> m
    marker_or      = marker_and:l wsp* 'or' marker_and:r -> ('or', l, r)
                       | marker_and:m -> m
    marker         = marker_or
    quoted_marker  = ';' wsp* marker
    identifier_end = letterOrDigit | (('-' | '_' | '.' )* letterOrDigit)
    identifier     = < letterOrDigit identifier_end* >
    name           = identifier
    extras_list    = identifier:i (wsp* ',' wsp* identifier)*:ids -> [i] + ids
    extras         = '[' wsp* extras_list?:e wsp* ']' -> e
    name_req       = (name:n wsp* extras?:e wsp* versionspec?:v wsp* quoted_marker?:m
                      -> (n, e or [], v or [], m))
    url_req        = (name:n wsp* extras?:e wsp* urlspec:v (wsp+ | end) quoted_marker?:m
                      -> (n, e or [], v, m))
    specification  = wsp* ( url_req | name_req ):s wsp* -> s
    # The result is a tuple - name, list-of-extras,
    # list-of-version-constraints-or-a-url, marker-ast or None


    URI_reference = <URI | relative_ref>
    URI           = scheme ':' hier_part ('?' query )? ( '#' fragment)?
    hier_part     = ('//' authority path_abempty) | path_absolute | path_rootless | path_empty
    absolute_URI  = scheme ':' hier_part ( '?' query )?
    relative_ref  = relative_part ( '?' query )? ( '#' fragment )?
    relative_part = '//' authority path_abempty | path_absolute | path_noscheme | path_empty
    scheme        = letter ( letter | digit | '+' | '-' | '.')*
    authority     = ( userinfo '@' )? host ( ':' port )?
    userinfo      = ( unreserved | pct_encoded | sub_delims | ':')*
    host          = IP_literal | IPv4address | reg_name
    port          = digit*
    IP_literal    = '[' ( IPv6address | IPvFuture) ']'
    IPvFuture     = 'v' hexdig+ '.' ( unreserved | sub_delims | ':')+
    IPv6address   = (
                      ( h16 ':'){6} ls32
                      | '::' ( h16 ':'){5} ls32
                      | ( h16 )?  '::' ( h16 ':'){4} ls32
                      | ( ( h16 ':')? h16 )? '::' ( h16 ':'){3} ls32
                      | ( ( h16 ':'){0,2} h16 )? '::' ( h16 ':'){2} ls32
                      | ( ( h16 ':'){0,3} h16 )? '::' h16 ':' ls32
                      | ( ( h16 ':'){0,4} h16 )? '::' ls32
                      | ( ( h16 ':'){0,5} h16 )? '::' h16
                      | ( ( h16 ':'){0,6} h16 )? '::' )
    h16           = hexdig{1,4}
    ls32          = ( h16 ':' h16) | IPv4address
    IPv4address   = dec_octet '.' dec_octet '.' dec_octet '.' dec_octet
    nz            = ~'0' digit
    dec_octet     = (
                      digit # 0-9
                      | nz digit # 10-99
                      | '1' digit{2} # 100-199
                      | '2' ('0' | '1' | '2' | '3' | '4') digit # 200-249
                      | '25' ('0' | '1' | '2' | '3' | '4' | '5') )# %250-255
    reg_name = ( unreserved | pct_encoded | sub_delims)*
    path = (
            path_abempty # begins with '/' or is empty
            | path_absolute # begins with '/' but not '//'
            | path_noscheme # begins with a non-colon segment
            | path_rootless # begins with a segment
            | path_empty ) # zero characters
    path_abempty  = ( '/' segment)*
    path_absolute = '/' ( segment_nz ( '/' segment)* )?
    path_noscheme = segment_nz_nc ( '/' segment)*
    path_rootless = segment_nz ( '/' segment)*
    path_empty    = pchar{0}
    segment       = pchar*
    segment_nz    = pchar+
    segment_nz_nc = ( unreserved | pct_encoded | sub_delims | '@')+
                    # non-zero-length segment without any colon ':'
    pchar         = unreserved | pct_encoded | sub_delims | ':' | '@'
    query         = ( pchar | '/' | '?')*
    fragment      = ( pchar | '/' | '?')*
    pct_encoded   = '%' hexdig
    unreserved    = letter | digit | '-' | '.' | '_' | '~'
    reserved      = gen_delims | sub_delims
    gen_delims    = ':' | '/' | '?' | '#' | '(' | ')?' | '@'
    sub_delims    = '!' | '$' | '&' | '\\'' | '(' | ')' | '*' | '+' | ',' | ';' | '='
    hexdig        = digit | 'a' | 'A' | 'b' | 'B' | 'c' | 'C' | 'd' | 'D' | 'e' | 'E' | 'f' | 'F'
"""


class Requirement():
    """
    Requirement parser
    """
    _parser = None
    _lookup: Dict[str, str] = dict(
        distro_codename=distro.codename(),
        distro_id=distro.id(),
        distro_like=distro.like(),
        distro_name=distro.name(),
        distro_version=distro.version(),
        os_name=os.name,
        platform_machine=platform.machine(),
        platform_python_implementation=platform.python_implementation(),
        platform_release=platform.release(),
        platform_system=platform.system(),
        platform_version=platform.version(),
        platform_full_version=platform.python_version(),
        python_version=platform.python_version()[:3],
        sys_platform=sys.platform
    )

    def __init__(self, s):
        self._parser = parsley.makeGrammar(GRAMMAR, {"lookup": self._lookup.__getitem__})
        self._parsed_requirement = self._parser(s).specification()

    @property
    def name(self):
        """
        Get the name part of the requirement
        """
        return self._parsed_requirement[0]

    @property
    def extra(self):
        """
        Get the extras from the requirement
        """
        return self._parsed_requirement[1]

    @property
    def version_evals(self):
        """
        Return the version evaluations for the requirement if present
        """
        if not self._parsed_requirement[2]:
            return []
        return self._parsed_requirement[2]

    @property
    def env_evals(self):
        """
        Return any environment evaluations for the requirement
        """
        if not self._parsed_requirement[3]:
            return []
        return self._parsed_requirement[3]

    @property
    def env_matches(self):
        """
        Determine if the current env matches the requirement

        Returns
        -------
        True if it matches
        """
        env_evals = list(self.env_evals)
        env_evals = self.evaluate_matches(env_evals)
        if len(env_evals) == 3:
            env_evals = [self.evaluate(*env_evals)]
        return False not in env_evals

    def evaluate_matches(self, env_evals):
        """
        Evaluate all of the statements and return a list of the results
        Parameters
        ----------
        env_evals: evals to be evaluated

        Returns
        -------
        Evaluates all the statements and return the ones that match
        """
        for element_num in range(len(env_evals)):  # pylint: disable=consider-using-enumerate
            entry = env_evals[element_num]
            if isinstance(entry, str):
                continue
            operation, val1, val2 = entry
            env_evals[element_num] = self.evaluate(operation, val1, val2)
        return env_evals

    def evaluate(self, operation, val1, val2):
        """Evaluate"""
        if isinstance(val1, tuple):
            val1 = self.evaluate(*val1)
        if isinstance(val2, tuple):
            val2 = self.evaluate(*val2)

        if isinstance(val1, str):
            val1 = pkg_resources.parse_version(val1)
        if isinstance(val2, str):
            val2 = pkg_resources.parse_version(val2)

        # statement = f'{val1} {operation} {val2}'

        result = None
        if operation == '>':
            result = val1 > val2
        elif operation == '<':
            result = val1 < val2
        elif operation == '>=':
            result = val1 >= val2
        elif operation == '<=':
            result = val1 <= val2
        elif operation == '==':
            result = val1 == val2
        elif operation in ['!', '!=']:
            result = val1 != val2
        elif operation == 'and':
            result = val1 and val2
        elif operation == 'or':
            result = val1 or val2
        else:
            logger.error(f'Invalid operation {operation}')
        # logger.debug(f'Evaluated {statement} == {result}')
        return result
