%setdefault('stylesheet', None)
%setdefault('navigation', False)
<!DOCTYPE html>
<html>
<head><title>{{prefix or 'Doorstop'}}</title>
  <meta charset="utf-8" />
  <meta http-equiv="content-type" content="text/html; charset=UTF-8" />
  <link rel="stylesheet" href="{{baseurl}}assets/doorstop/bootstrap.min.css" />
  <link rel="stylesheet" href="{{baseurl}}assets/doorstop/general.css" />
  {{! '<link type="text/css" rel="stylesheet" href="%s" />'%(baseurl+'assets/doorstop/'+stylesheet) if stylesheet else "" }}
</head>
<body prefix="{{prefix}}">
{{! '<P>Navigation: <a href="{0}">Home</a> &bull; <a href="{0}documents">Documents</a>'.format(baseurl) if navigation else ''}}
  {{!base}}
</body>
</html>
