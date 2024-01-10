% rebase('base.tpl', title='Doorstop', stylesheet='sidebar.css')
<div class="container-fluid">
    <div class="row">
      <div class="col-lg-2 hidden-sm hidden-xs">
          <nav id="TOC" class="nav nav-stacked fixed sidebar">
              {{!toc}}
          </nav>
      </div>
      <div class="col-lg-8" id="main">
        {{!body}}
      </div>
    </div>
</div>
<!-- jQuery (necessary for Bootstrap's JavaScript plugins) -->
<script src="{{baseurl}}template/jquery.min.js"></script>
<script src="{{baseurl}}template/bootstrap.min.js"></script>
<script>
    $(function() {
        $("table").addClass("table");
        $("nav ul").addClass("nav nav-stacked");
        $("nav").affix();
        $('body').scrollspy({
          target: '.sidebar'
        });
        $("#main a").attr("target", "parent");

  $(window).on('hashchange', function() {
    $(window).scrollTop();});
  });
</script>