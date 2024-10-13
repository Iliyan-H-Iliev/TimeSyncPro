document.addEventListener('DOMContentLoaded', function () {
    // Function to handle smooth scrolling to the target element
    function scrollToElement(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            const headerOffset = 100; // Adjust this value to offset for your sticky header
            const elementPosition = element.getBoundingClientRect().top;
            const offsetPosition = elementPosition + window.scrollY - headerOffset;

            window.scrollTo({
                top: offsetPosition,
                behavior: 'smooth'
            });
        }
    }

    // Check for the 'scroll' parameter in the URL
    const urlParams = new URLSearchParams(window.location.search);
    const scrollTarget = urlParams.get('scroll');
    if (scrollTarget) {
        // Delay the scroll slightly to ensure the page has fully loaded
        setTimeout(() => scrollToElement(scrollTarget), 100);
    }
});