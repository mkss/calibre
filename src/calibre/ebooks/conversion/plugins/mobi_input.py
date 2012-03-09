from __future__ import with_statement
__license__ = 'GPL 3'
__copyright__ = '2009, Kovid Goyal <kovid@kovidgoyal.net>'
__docformat__ = 'restructuredtext en'

import os

from calibre.customize.conversion import InputFormatPlugin

class MOBIInput(InputFormatPlugin):

    name        = 'MOBI Input'
    author      = 'Kovid Goyal'
    description = 'Convert MOBI files (.mobi, .prc, .azw) to HTML'
    file_types  = set(['mobi', 'prc', 'azw'])

    def convert(self, stream, options, file_ext, log,
                accelerators):

        if os.environ.get('USE_MOBIUNPACK', None) is not None:
            from calibre.ptempfile import PersistentTemporaryDirectory
            try:
                from mobiunpack.mobi_unpack import Mobi8Reader
                from calibre.customize.ui import plugin_for_input_format

                wdir = PersistentTemporaryDirectory('_unpack_space')
                m8r = Mobi8Reader(stream, wdir)
                if m8r.isK8():
                    epub_path = m8r.processMobi8()
                    epub_input = plugin_for_input_format('epub')
                    for opt in epub_input.options:
                        setattr(options, opt.option.name, opt.recommended_value)
                    options.input_encoding = m8r.getCodec()
                    return epub_input.convert(open(epub_path,'rb'), options,
                            'epub', log, accelerators)
            except Exception:
                log.exception('mobi_unpack code not working')

        from calibre.ebooks.mobi.reader.mobi6 import MobiReader
        from lxml import html
        parse_cache = {}
        try:
            mr = MobiReader(stream, log, options.input_encoding,
                        options.debug_pipeline)
            if mr.kf8_type is None:
                mr.extract_content(u'.', parse_cache)

        except:
            mr = MobiReader(stream, log, options.input_encoding,
                        options.debug_pipeline, try_extra_data_fix=True)
            if mr.kf8_type is None:
                mr.extract_content(u'.', parse_cache)

        if mr.kf8_type is not None:
            from calibre.ebooks.mobi.reader.mobi8 import Mobi8Reader
            return os.path.abspath(Mobi8Reader(mr, log)())

        raw = parse_cache.pop('calibre_raw_mobi_markup', False)
        if raw:
            if isinstance(raw, unicode):
                raw = raw.encode('utf-8')
            open(u'debug-raw.html', 'wb').write(raw)
        for f, root in parse_cache.items():
            with open(f, 'wb') as q:
                q.write(html.tostring(root, encoding='utf-8', method='xml',
                    include_meta_content_type=False))
                accelerators['pagebreaks'] = '//h:div[@class="mbp_pagebreak"]'
        return mr.created_opf_path
