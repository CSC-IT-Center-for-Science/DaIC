var Files = {};

Files.containerId = _.last(window.location.pathname.split("/"));

Files.File = Backbone.Model.extend({
    defaults: {
        name: '',
        uuid: '',
    }
});

Files.Collection = Backbone.Collection.extend({
    url: ['/v1/containers', Files.containerId].join("/"),
    model: Files.File,
    parse: function(response) {
        if (_.has(response, "files")) {
            return response["files"];
        } else {
            return [];
        }
    }
});

Files.Views = {};

Files.Views.Edit = Backbone.View.extend({
    change: function () {
        console.log("change");
        this.model.set({
            name: $(this.el).children('input').val()
        });
        this.model.save();
    },
    destroy: function () {
         console.log("destroy");
        var el = this.el;
        this.model.destroy({
            success: function () {
                console.log("delete ok");
                $(el).remove();
            }
        });
    },
    events: {
        'click .btn-download': 'open',
        'click .btn-remove': 'destroy',
        'change input': 'change'
    },

    open: function() {
        window.open(['/v1/containers', Files.containerId, 'files', this.model.get("uuid"), "download"].join("/"));
    },

    initialize: function () {
        _(this).bindAll('change', 'destroy', 'render');
    },
    render: function () {
        $('#file-template').tmpl(this.model.toJSON()).appendTo(this.el);
        this.delegateEvents();
    }
});

Files.Views.List = Backbone.View.extend({
    append: function (model) {
        var p = $('<div class="row">').appendTo('#files'),
            view = new Files.Views.Edit({
                model: model,
                el: p[0]
            });
        view.render();
    },
    initialize: function () {
        _(this).bindAll('append', 'render');
        this.collection.bind('refresh', this.render);
        this.collection.bind('add', this.append);
    },
    render: function () {
        $('#containers').empty();
        this.collection.each(function (model) {
            this.append(model);
        }, this);
    }
});

$(function () {
    var collection = new Files.Collection(),
        view = new Files.Views.List({
            collection: collection
        });

    collection.fetch();

});
