var Containers = {};

Containers.Container = Backbone.Model.extend({
    defaults: {
        name: '',
    }
});

Containers.Collection = Backbone.Collection.extend({
    model: Containers.Container,
    url: '/v1/containers'
});

Containers.Views = {};

Containers.Views.Edit = Backbone.View.extend({
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
        'click .btn-collection-remove': 'destroy',
    },
    initialize: function () {
        _(this).bindAll('destroy', 'render');
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
    var collection = new Containers.Collection();
    var view = new Containers.Views.List({
        collection: collection
    });
    collection.fetch();
});
