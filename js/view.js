
$(window).scroll(function(e){ 
	$el = $('.fixattop'); 
	height = $('#header_wrap').height()
	
	if ($(this).scrollTop() > height && $el.css('position') != 'fixed'){ 
		$('.fixattop').css({'position': 'fixed'}); 
	}
	if ($(this).scrollTop() < height && $el.css('position') == 'fixed'){
		$('.fixattop').css({'position': 'relative'}); 
	} 
});