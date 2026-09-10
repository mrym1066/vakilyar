/*total_amount range*/

 $('#sl2').slider();

	var RGBChange = function() {
	  $('#RGB').css('background', 'rgb('+r.getValue()+','+g.getValue()+','+b.getValue()+')')
	};	
		
/*scroll to top*/

$(document).ready(function(){
	$(function () {
		$.scrollUp({
	        scrollName: 'scrollUp', // Element ID
	        scrollDistance: 300, // Distance from top/bottom before showing element (px)
	        scrollFrom: 'top', // 'top' or 'bottom'
	        scrollSpeed: 300, // Speed back to top (ms)
	        easingType: 'linear', // Scroll to top easing (see http://easings.net/)
	        animation: 'fade', // Fade, slide, none
	        animationSpeed: 200, // Animation in speed (ms)
	        scrollTrigger: false, // Set a custom triggering element. Can be an HTML string or jQuery object
					//scrollTarget: false, // Set a custom target element for scrolling to the top
	        scrollText: '<i class="fa fa-angle-up"></i>', // Text for element, can contain HTML
	        scrollTitle: false, // Set a custom <a> title if required.
	        scrollImg: false, // Set true to use image
	        activeOverlay: false, // Set CSS color to display scrollUp active point, e.g '#00FFFF'
	        zIndex: 2147483647 // Z-Index for the overlay
		});
	});
});




function updatetotal_amount(container, n) {
   //container -> each one of the $('.cd-gallery').children('li')
   //n -> index of the selected item in the .cd-item-wrapper
   var total_amountTag = container.find('.cd-total_amount'),
       selectedItem = container.find('.cd-item-wrapper li').eq(n);
   if( selectedItem.data('sale') ) { 
      // if item is on sale - cross old total_amount and add new one
      total_amountTag.addClass('on-sale');
      var newtotal_amountTag = ( total_amountTag.next('.cd-new-total_amount').length > 0 ) ? total_amountTag.next('.cd-new-total_amount') : $('<em class="cd-new-total_amount"></em>').insertAfter(total_amountTag);
      newtotal_amountTag.text(selectedItem.data('total_amount'));
      setTimeout(function(){ newtotal_amountTag.addClass('is-visible'); }, 100);
   } else {
      // if item is not on sale - remove cross on old total_amount and sale total_amount
      total_amountTag.removeClass('on-sale').next('.cd-new-total_amount').removeClass('is-visible').on('webkitTransitionEnd otransitionend oTransitionEnd msTransitionEnd transitionend', function(){
         total_amountTag.next('.cd-new-total_amount').remove();
      });
   }
}