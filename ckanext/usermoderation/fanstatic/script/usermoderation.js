this.ckan.module('promo-more', {
  options: {
    'vitems': 3,
    'more': 'Read more',
    'less': 'Hide',
  },

  initialize: function () {
    var promo = this.el.children();
    if (promo.length > this.options['vitems']){
      var container = jQuery('<div>').addClass('promo-container').append(promo.slice(this.options['vitems']));
      var readMore = jQuery('<a>').addClass('promo-read-more').addClass('btn').text(this.options.more).on('click', {'container': container, 'self': this}, this.promoReadMore);
      
      this.el.append(container, readMore);
    }
  },

  promoReadMore: function (event) {
      var _this = jQuery(this);
      var promo = event.data.container;
      var opt = event.data.self.options;
      if (promo.hasClass('more')){
        promo.slideUp();
        _this.text(opt.more)
      } else{
        promo.slideDown();
        _this.text(opt.less)
      }
      promo.toggleClass('more');
  },

});

this.ckan.module('request-account', {
  options: {
    confirm: 'Your request will be processed soon and you will get a notification to the specified email',
  },

  initialize: function () {
      jQuery.proxyAll(this, /_on/);
      this.el.popover({ html: true,
                       content: 'Loading...', placement: 'right'});
      this.el.on('click', this._onClick);
    },

    _snippetReceived: false,

    _onClick: function(event) {
        if (!this._snippetReceived) {
            this.sandbox.client.getTemplate('request_account.html',
                                            this.options,
                                            this._onReceiveSnippet);
            this._snippetReceived = true;
        }

    },


    _onReceiveSnippet: function(html) {
      this.el.popover('destroy');
      this.el.popover({ html: true,
                       content: html, placement: 'right'});
      this.el.popover('show');
      var form = this.el.parent().find('form')
      jQuery('[name="admin"]',form).val(this.options.href);
      form.on('submit', { parent: this}, this.onRequest);
    },

    onRequest: function (event) {
        var _jq = jQuery || $
        var self = jQuery(this)
        jQuery('button', self).text('Processing..');
        var postData = self.serializeArray();
        var formURL = self.attr("action");
        var parent = event.data.parent;
        jQuery.ajax(
        {
            url : formURL,
            type: "POST",
            data : postData,
            success:function(data, textStatus, jqXHR) 
            {   
                parent.el.popover('destroy').popover({ html: true,
                       content: parent.options.confirm, placement: 'right'}).popover('show');
                setTimeout(function () {
                  parent.el.popover('destroy');
                  parent._snippetReceived = false
                }, 2000);
            },
            error: function(jqXHR, textStatus, errorThrown) 
            {
                console.log(jqXHR.status);
                if (jqXHR.status == 400){
                  jQuery('button', self).text('Email or username already used');
                }
                else jQuery('button', self).text('Error');
            }
        });
        event.preventDefault && event.preventDefault(); //STOP default action
        event.stop && event.stop()
        event.stopPropagation && event.stopPropagation();
        event.returnValue = false;
        console.log(event.defaultPrevented);
        return false
    }
});


this.ckan.module('account-request-manage', {
  options: {
  },

  initialize: function () {
    jQuery.proxyAll(this, /_on/);
    this.el.on('click', this._onClick);
  },

  _onClick: function (event) {
    var self = this;
    var row = this.el.closest('tr');
    var action = this.options.action;
    var user_id = this.options.id;
    var agency = row.find('#agency').val();
    var role = row.find('#role').val();
    jQuery.ajax(
      {
        url : this.options.href,
        type: "POST",
        data : {'action':action, 'id': user_id, 'agency': agency, 'role': role},
        success:function(data, textStatus, jqXHR) 
        {   

          if (action=='approve'){
            row.addClass('management-approve');
            jQuery('.btn', row).attr('disabled', 'disabled').removeClass('btn-info btn-success');
          } else {
            row.remove();
          }
        },
        error: function(jqXHR, textStatus, errorThrown) 
        {
            row.addClass('management-error');
            self.el.popover({ content: 'Operation is not completed', placement: 'top'}).popover('show');
            setTimeout(function () {
              self.el.popover('destroy');
            }, 4000);
        }
      }
    );
  }

});

