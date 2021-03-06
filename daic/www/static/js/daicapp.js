var Containers = {};

Containers.Collection = Backbone.Collection.extend({
    url: '/v1/containers'
});

Containers.Views = {};

Containers.Views.Edit = Backbone.View.extend({
    change: function () {
        console.log("change");
        this.model.set({
            name: $(this.el).children('input').val()
        });
        this.model.save();
    },
    destroy: function () {
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
        window.open('/v1/containers/download/'+this.model.get("id"));
    },

    initialize: function () {
        _(this).bindAll('change', 'destroy', 'render');
    },
    render: function () {
        $('#container-template').tmpl(this.model.toJSON()).appendTo(this.el);
        this.delegateEvents();
    }
});

Containers.Views.List = Backbone.View.extend({
    append: function (model) {
        var p = $('<div class="row">').appendTo('#containers'),
            view = new Containers.Views.Edit({
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
    var collection = new Containers.Collection(),
        view = new Containers.Views.List({
            collection: collection
        });

    collection.fetch();

});
