%setdefault('stylesheet', None)
%setdefault('navigation', False)
<!DOCTYPE html>
<html>
<head><title>{{title or 'Doorstop'}}</title>
  <meta charset="utf-8" />
  <meta http-equiv="content-type" content="text/html; charset=UTF-8" />
  <link rel="stylesheet" href="{{baseurl}}template/bootstrap.min.css" />
  <link rel="stylesheet" href="{{baseurl}}template/general.css" />
  {{! '<link type="text/css" rel="stylesheet" href="%s" />'%(baseurl+'template/'+stylesheet) if stylesheet else "" }}
  <script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.5/MathJax.js?config=TeX-MML-AM_CHTML" ></script>
  <script type="text/x-mathjax-config">
  MathJax.Hub.Config({
    tex2jax: {inlineMath: [["$","$"],["\\(","\\)"]]}
  });
  </script>
</head>
<body>
{{! '<P>Navigation: <a href="{0}">Home</a> &bull; <a href="{0}documents/">Documents</a>'.format(baseurl) if navigation else ''}}
  {{!base}}
</body>
</html>
