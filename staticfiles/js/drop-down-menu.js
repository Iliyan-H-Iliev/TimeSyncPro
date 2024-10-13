document.addEventListener('DOMContentLoaded', (event) => {
    const dropdownToggle = document.getElementById('navbarDropdown');
    const dropdownMenu = dropdownToggle.nextElementSibling;
    const image = dropdownToggle.querySelector('.rounded-circle');

    const showMenu = () => {
        dropdownMenu.style.display = 'block';
        image.classList.add('hovered');
    };

    const hideMenu = (e) => {
        if (!dropdownToggle.contains(e.relatedTarget) && !dropdownMenu.contains(e.relatedTarget)) {
            dropdownMenu.style.display = 'none';
            image.classList.remove('hovered');
        }
    };

    dropdownToggle.addEventListener('mouseover', showMenu);
    dropdownToggle.addEventListener('mouseout', hideMenu);
    dropdownMenu.addEventListener('mouseover', showMenu);
    dropdownMenu.addEventListener('mouseout', hideMenu);
});