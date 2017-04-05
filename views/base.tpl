<!DOCTYPE html>
<html>
<head><title>{{title or 'Doorstop'}}</title>
  <meta charset="utf-8" />
  <meta http-equiv="content-type" content="text/html; charset=UTF-8" />
  <link rel="stylesheet" href="{{baseurl}}/assets/doorstop/bootstrap.min.css" />
  <link rel="stylesheet" href="{{baseurl}}/assets/doorstop/general.css" />
  {{! '<link type="text/css" rel="stylesheet" href="%s" />'%(baseurl+'/assets/doorstop/'+stylesheet) if stylesheet else "" }}
</head>
<body>
  <P>Navigation: <a href="{{baseurl}}/">Home</a> &bull; <a href="{{baseurl}}/documents/">Documents</a>
  {{!base}}
</body>
</html>
