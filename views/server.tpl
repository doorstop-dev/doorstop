% rebase('base.tpl', stylesheet='sidebar.css')
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

<!-- Button trigger modal -->
    <div class="modal fade" tabindex="-1" role="dialog" id="editItemModal">
    <div class="modal-dialog modal-lg" role="document">
        <div class="modal-content">
        <div class="modal-header">
            <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
            <h4 class="modal-title">Edit item</h4>
        </div>
        <div class="modal-body">
            <form id="editItemForm" method="post">
                <input type="hidden" class="form-control" id="uid"></input>
                <input type="hidden" class="form-control" id="prefix"></input>
                <div class="form-group">
                    <label for="itemtext">Item Text</label>
                    <textarea class="form-control" rows=10 name="itemtext" id="itemtext"></textarea>
                </div>
                <div class="form-group">
                    <label for="level">Level</label>
                    <input class="form-control" name="level" id="level"></input>
                </div>
                <div class="form-group">
                    <div class="checkbox">
                        <label>
                            <input type="checkbox" name="normative" id="normative"> Normative
                        </label>
                    </div>
                </div>
                <div class="form-group">
                    <div class="checkbox">
                        <label>
                            <input type="checkbox" name="derived" id="derived"> Derived
                        </label>
                    </div>
                </div>
                <div class="form-group">
                    <label for="links">Item Links</label>
                    <input class="form-control" name="links" id="links"></input>
                </div>
                <div class="form-group">
                    <label for="message">Commit message</label>
                    <input class="form-control" name="message" id="message"></input>
                </div>
            </form>
        </div>
        <div class="modal-footer">
            <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
            <button type="button" class="btn btn-primary" id="submit">Save changes</button>
        </div>
        </div><!-- /.modal-content -->
    </div><!-- /.modal-dialog -->
    </div><!-- /.modal -->

</div>
<!-- jQuery (necessary for Bootstrap's JavaScript plugins) -->
<script src="{{baseurl}}assets/doorstop/js/jquery.min.js"></script>
<script src="{{baseurl}}assets/doorstop/js/bootstrap.min.js"></script>
<script>
    $( document ).ready(function() {
        $("table").addClass("table")
        $("nav").affix()
        $("nav ul").addClass("nav nav-stacked")
        $('body').scrollspy({
          target: '.sidebar'
        });
        // $("#main a").attr("target", "parent");

        $(window).on('hashchange', function() {
            $(window).scrollTop($(location.hash).offset().top)});        

        $('#editItemModal').on('show.bs.modal', function (event) {
            var button = $(event.relatedTarget)
            var uid = button.data('uid')
            var prefix = $("body").attr("prefix")
            var modal = $(this)
            modal.find("#uid").val(uid)
            modal.find(".modal-title").val("Edit item " + uid)
            var url = "/documents/" + prefix + "/items/" + uid + '?format=json'
            $.ajax({url:url,
                    context:modal}).done(function(data){
                        var textarea = modal.find('.modal-body texarea')
                        $("#editItemModal textarea").val(data.text)
                        $("#editItemModal #links").val(data.links)
                        $("#editItemModal #level").val(data.level)
                        if (data.normative){$("#normative").prop("checked", true)}
                        if (data.derived){$("#derived").prop("checked", true)}
                    })
        })

        $('button#submit').click(function () {
            //Save the edits
            var modal = $("#editItemModal")
            var uid = modal.find('#uid').val()
            var prefix = $("body").attr("prefix")
            var url = "/documents/" + prefix + "/items/" + uid
            $.ajax({url:url,
                    method:'POST',
                    data: $('#editItemForm').serialize()}).done(function(data){
                        if (data.result == "ok") { location.reload() }
                    })
        });

        $('[data-tooltip="tooltip"]').tooltip();

        $("#main :header").each(function(){
            
            var button = '<div class="btn-group" role="group">'
            button = button + '<button type="button" class="btn btn-default" data-toggle="modal" data-tooltip="tooltip" title="Edit item" data-target="#editItemModal" '
            button = button + 'data-uid="' + $(this).attr("id") +'"><span class="glyphicon glyphicon-pencil"></span></button>'
            button = button + '<button type="button" class="btn btn-default insert" data-tooltip="tooltip" title="Insert after"'
            button = button + 'id="' + $(this).attr("id") +'"><span class="glyphicon glyphicon-plus"></span></button>'
            button = button + '<button type="button" class="btn btn-default delete" data-tooltip="tooltip" title="Delete"'
            button = button + 'id="' + $(this).attr("id") +'"><span class="glyphicon glyphicon-remove"></span></button>'
            button = button + '</div>'
            $(this).append(button)
        })

       $('.insert').on('click', function (e) {
        console.log($(this).attr("id"))
        var prefix = $("body").attr("prefix")
        $.ajax({url:"/documents/" + prefix + "/items",
                method:'POST',
                data: {uid:$(this).attr("id")}}).done(function(data){
                    console.log(data)
                    if (data.result == "ok") { location.reload() }
                    })
        });

       $('.delete').on('click', function (e) {
        var prefix = $("body").attr("prefix")
        $.ajax({url:"/documents/" + prefix + "/items/" + $(this).attr("id"),
                method:'DELETE'}).done(function(data){
                    if (data.result == "ok") { location.reload() }
                    else alert("Delete failed")
                    })
        });
    });


</script>
</body>
</html>


