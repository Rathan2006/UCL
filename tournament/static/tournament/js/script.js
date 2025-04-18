document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Add active class to current nav link
    var path = window.location.pathname;
    document.querySelectorAll('.nav-link').forEach(function(link) {
        var linkPath = link.getAttribute('href');
        if (linkPath && path.startsWith(linkPath)) {
            link.classList.add('active');
        }
    });
    
    // Handle match result form
    var resultSelect = document.getElementById('id_result');
    var manOfMatchSelect = document.getElementById('id_man_of_the_match');
    
    if (resultSelect && manOfMatchSelect) {
        resultSelect.addEventListener('change', function() {
            if (this.value === 'TBD' || this.value === 'No Result') {
                manOfMatchSelect.disabled = true;
                manOfMatchSelect.value = '';
            } else {
                manOfMatchSelect.disabled = false;
            }
        });
        
        // Initialize state based on current value
        if (resultSelect.value === 'TBD' || resultSelect.value === 'No Result') {
            manOfMatchSelect.disabled = true;
        }
    }
    
    // Initialize DataTables if present
    if (typeof $.fn.DataTable !== 'undefined') {
        $('.datatable').DataTable({
            "pageLength": 25,
            "responsive": true
        });
    }
    
    // WebSocket connection for live matches
    if (typeof WebSocket !== 'undefined' && document.getElementById('home-score')) {
        const matchId = document.currentScript.getAttribute('data-match-id') || 
                       (window.location.pathname.match(/match\/(\d+)/) ? window.location.pathname.match(/match\/(\d+)/)[1] : null);
        
        if (matchId) {
            const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
            const matchSocket = new WebSocket(
                protocol + window.location.host +
                '/ws/match/' + matchId + '/'
            );

            matchSocket.onmessage = function(e) {
                try {
                    const data = JSON.parse(e.data);
                    if (data.home_score !== undefined) $('#home-score').text(data.home_score);
                    if (data.away_score !== undefined) $('#away-score').text(data.away_score);
                    if (data.current_batsman !== undefined) $('#current-batsman').text(data.current_batsman);
                    if (data.current_bowler !== undefined) $('#current-bowler').text(data.current_bowler);
                    if (data.balls_remaining !== undefined) $('#balls-remaining').text(data.balls_remaining);
                    if (data.innings !== undefined) $('#innings').text(data.innings);
                } catch (error) {
                    console.error('Error processing WebSocket message:', error);
                }
            };

            matchSocket.onclose = function(e) {
                if (!e.wasClean) {
                    console.error('Match socket closed unexpectedly:', e.reason);
                    // Attempt to reconnect after 5 seconds
                    setTimeout(function() {
                        initializeWebSocket(matchId);
                    }, 5000);
                }
            };

            matchSocket.onerror = function(error) {
                console.error('WebSocket error:', error);
            };

            // When admin submits score update form
            $('#score-update-form').off('submit').on('submit', function(e) {
                e.preventDefault();
                if (matchSocket.readyState === WebSocket.OPEN) {
                    const formData = $(this).serializeArray();
                    const updateData = {};
                    
                    $.each(formData, function(_, field) {
                        updateData[field.name] = field.value;
                    });
                    
                    try {
                        matchSocket.send(JSON.stringify({
                            'message': updateData
                        }));
                    } catch (error) {
                        console.error('Error sending WebSocket message:', error);
                        // Fallback to AJAX if WebSocket fails
                        $.post(window.location.pathname + '/update', $(this).serialize());
                    }
                } else {
                    // Fallback to AJAX if WebSocket is not open
                    $.post(window.location.pathname + '/update', $(this).serialize());
                }
            });
        }
    }
});