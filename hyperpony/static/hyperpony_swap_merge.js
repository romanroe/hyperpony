htmx.defineExtension('merge', {
    isInlineSwap: function (swapStyle) {
        return swapStyle === 'merge';
    },
    handleSwap: function (swapStyle, target, fragment) {
        let result = undefined;
        if (swapStyle === 'merge' || swapStyle === 'merge:outerHTML') {
            result = Idiomorph.morph(target, fragment.children, {
                morphStyle: 'outerHTML',
                ignoreActive: true
            });
        } else if (swapStyle === 'merge:innerHTML') {
            result = Idiomorph.morph(target, fragment.children, {
                morphStyle: 'innerHTML',
                ignoreActive: true
            });
        }
        return result;
    }
});
