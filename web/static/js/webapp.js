document.addEventListener('DOMContentLoaded', function() {
    const tg = window.Telegram.WebApp;
    tg.expand();

    // Все наши экраны
    const step0 = document.getElementById('step-0');
    const step1 = document.getElementById('step-1');
    const step2 = document.getElementById('step-2');
    const step3 = document.getElementById('step-3');

    // Списки, куда мы будем добавлять кнопки
    const servicesList = document.getElementById('services-list');
    const mastersList = document.getElementById('masters-list');
    const timeSlotsList = document.getElementById('time-slots-list');
    const datePicker = document.getElementById('date-picker');

    // Переменные для хранения выбора
    let selectedServiceId = null;
    let selectedMasterId = null;
    let selectedDate = null;
    let selectedTime = null;

    const allWorkSlots = ['10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00'];

    // МАГИЯ ПРОТИВ NGROK: Секретный заголовок, чтобы он не блокировал API запросы
    const fetchOptions = {
        headers: {
            'ngrok-skip-browser-warning': 'true'
        }
    };

    // 0. ЗАГРУЗКА УСЛУГ
    fetch('/api/services/', fetchOptions)
        .then(res => res.json())
        .then(data => {
            data.forEach(service => {
                const btn = document.createElement('button');
                btn.textContent = service.name;
                btn.className = 'action-btn';
                btn.addEventListener('click', function() {
                    selectedServiceId = service.id;
                    step0.style.display = 'none';
                    step1.style.display = 'block';
                });
                servicesList.appendChild(btn);
            });
        })
        .catch(error => console.error('Ошибка загрузки услуг:', error));

    // 1. ЗАГРУЗКА МАСТЕРОВ
    fetch('/api/masters/', fetchOptions)
        .then(res => res.json())
        .then(data => {
            data.forEach(master => {
                const btn = document.createElement('button');
                btn.textContent = master.name;
                btn.className = 'master-btn';
                btn.addEventListener('click', function() {
                    selectedMasterId = master.id;
                    document.getElementById('selected-master-title').textContent = 'Мастер: ' + master.name;
                    step1.style.display = 'none';
                    step2.style.display = 'block';
                });
                mastersList.appendChild(btn);
            });
        })
        .catch(error => console.error('Ошибка загрузки мастеров:', error));

    // 2. ВЫБОР ДАТЫ И ЗАГРУЗКА ВРЕМЕНИ
    document.getElementById('btn-next').addEventListener('click', function() {
        selectedDate = datePicker.value;
        if (!selectedDate) {
            alert('Пожалуйста, выберите дату!');
            return;
        }

        step2.style.display = 'none';
        step3.style.display = 'block';
        timeSlotsList.innerHTML = ''; // Очищаем старые кнопки или сообщения

        fetch(`/get-booked-slots/?master_id=${selectedMasterId}&date=${selectedDate}`, fetchOptions)
            .then(res => res.json())
            .then(data => {
                // 🔥 НОВАЯ ЛОГИКА: ПРОВЕРКА НА ВЫХОДНОЙ
                if (data.day_off === true) {
                    timeSlotsList.innerHTML = '<p style="text-align: center; margin-top: 20px; font-weight: bold;">🌴 Мастер в этот день отдыхает.<br>Пожалуйста, нажмите "Назад" и выберите другую дату.</p>';
                    return; // Останавливаем выполнение функции, кнопки времени не рисуем!
                }

                // СТАРАЯ ЛОГИКА: ЕСЛИ ДЕНЬ РАБОЧИЙ, РИСУЕМ ВРЕМЯ
                let rawBookedSlots = data.booked || data.booked_slots || data.booked_times || [];
                const bookedSlots = rawBookedSlots.map(time => time.substring(0, 5));

                allWorkSlots.forEach(slot => {
                    const btn = document.createElement('button');
                    btn.className = 'time-btn';

                    if (bookedSlots.includes(slot)) {
                        btn.textContent = slot + ' (Занято)';
                        btn.disabled = true;
                    } else {
                        btn.textContent = slot;
                        btn.addEventListener('click', function() {
                            selectedTime = slot;

                            const bookingData = {
                                service_id: selectedServiceId,
                                master_id: selectedMasterId,
                                date: selectedDate,
                                time: selectedTime
                            };

                            tg.sendData(JSON.stringify(bookingData));
                        });
                    }
                    timeSlotsList.appendChild(btn);
                });
            })
            .catch(err => {
                console.error('Ошибка загрузки расписания:', err);
                timeSlotsList.innerHTML = '<p>Ошибка загрузки расписания :(</p>';
            });
    });

    // 3. ЛОГИКА КНОПОК "НАЗАД"
    document.getElementById('btn-back-to-services').addEventListener('click', function() {
        step1.style.display = 'none';
        step0.style.display = 'block';
    });

    document.getElementById('btn-back-to-masters').addEventListener('click', function() {
        step2.style.display = 'none';
        step1.style.display = 'block';
    });

    document.getElementById('btn-back-to-date').addEventListener('click', function() {
        step3.style.display = 'none';
        step2.style.display = 'block';
    });
});