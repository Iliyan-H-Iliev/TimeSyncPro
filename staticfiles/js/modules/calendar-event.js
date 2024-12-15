document.addEventListener('DOMContentLoaded', function () {
    var calendarEl = document.getElementById('calendar');
    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        editable: false,
        selectable: false,
        events: function (info, successCallback, failureCallback) {
            fetch(`/api/events/?start=${info.startStr}&end=${info.endStr}`)
                .then(response => response.json())
                .then(data => {
                    let events = [];

                    // Working days with time
                    data.workingDays.forEach(workDay => {
                        events.push({
                            title: `${workDay.start_time}-${workDay.end_time}`,
                            start: workDay.date,
                            allDay: true,
                            backgroundColor: '#3788d8',
                            borderColor: '#3788d8',

                        });
                    });

                    // Holidays
                    data.holidays.forEach(holiday => {
                        events.push({
                            title: holiday.title,
                            start: holiday.date,
                            backgroundColor: '#2ecc71',
                            borderColor: '#2ecc71'
                        });
                    });

                    // Absences
                    data.absences.forEach(absence => {
                        events.push({
                            title: absence.title,
                            start: absence.start_date,
                            end: absence.end_date,
                            backgroundColor: '#e74c3c',
                            borderColor: '#e74c3c'
                        });
                    });

                    // Simple days off
                    data.daysOff.forEach(date => {
                        events.push({
                            title: 'Off',
                            start: date,
                            allDay: true,
                            backgroundColor: '#f39c12',
                            borderColor: '#f39c12'
                        });
                    });

                    successCallback(events);
                })
                .catch(error => {
                    console.error('Error:', error);
                    failureCallback(error);
                });
        },
        eventClick: function (info) {
            // Enhanced event click handler
            let eventDetails = `${info.event.title}`;
            if (info.event.classNames.includes('working-day')) {
                const startTime = info.event.start.toLocaleTimeString();
                const endTime = info.event.end.toLocaleTimeString();
                eventDetails += `\nTime: ${startTime} - ${endTime}`;
            }
            alert(eventDetails);
        }
    });

    calendar.render();
});