
# XXX Make technical regexes more correct.

DOMAIN_NAME_PART = r'(?: [^.\s]+ )'
FQDN = rf'''
        (?:
          {DOMAIN_NAME_PART}
          (?: [.] {DOMAIN_NAME_PART} )*
          )
        '''
EMAIL = rf'''
        (?:
          [^@\s]+  # user/alias
          [@]
          {FQDN}
          )
        '''
URL = rf'''
        (?:
          (?:
            (?: [^:]+ [:] )?  # scheme
            [/] [/]
            )?
          {FQDN}
          (?:
            [#] [^?\s]+  # fragments
            )?
          (?:
            [?] \S+  # query
            )?
          )
        '''
