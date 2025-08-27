%setdefault('stylesheet', None)
%setdefault('navigation', False)
<!DOCTYPE html>
<html>
<head><title>{{!doc_attributes["name"]}}</title>
  <meta charset="utf-8" />
  <meta http-equiv="content-type" content="text/html; charset=UTF-8" />
  % if is_doc:
  %   tmpRef='../'
  % else:
  %   tmpRef=''
  % end
  <link rel="stylesheet" href="{{baseurl}}{{tmpRef}}template/bootstrap.min.css" />
  <link rel="stylesheet" href="{{baseurl}}{{tmpRef}}template/general.css" />
  {{! '<link type="text/css" rel="stylesheet" href="%s" />'%(baseurl+tmpRef+'template/'+stylesheet) if stylesheet else "" }}
  <style>
    .dropdown-menu-scrollable {
        max-height: 50vh; /* 50% der Viewport-Höhe */
        overflow-y: auto;
        overflow-x: hidden; /* Horizontalen Scrollbalken verhindern */
    }
  </style>
  <script src="{{baseurl}}{{tmpRef}}template/tex-mml-chtml.js" id="MathJax-script" async></script>
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
