function getActionBadgeClass(action) {
    const classes = {
        'create': 'success',
        'update': 'primary',
        'delete': 'danger',
        'register': 'info',
    };
    return classes[action] || 'secondary';
}
