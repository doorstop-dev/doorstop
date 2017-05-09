% rebase('base.tpl', title='Doorstop')
<H1>Doorstop - List of documents</H1>
<P>
<ul>
{{! "".join('<li><a href="/documents/{0}/">{0}</a></li>'.format(p) for p in prefixes) }}
</ul>
</code>
