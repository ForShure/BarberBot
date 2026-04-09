document.addEventListener('DOMContentLoaded', function() {

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    const tg = window.Telegram.WebApp;

    // 🔥 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ
    tg.ready();
    tg.expand();

    const debugDiv = document.createElement('div');
    debugDiv.style.cssText = "background: yellow; color: black; padding: 10px; font-weight: bold; font-size: 14px; word-wrap: break-word;";

    debugDiv.innerHTML = "ТГ: " + JSON.stringify(tg.initDataUnsafe) + "<br><br>URL: " + window.location.href;
    document.body.prepend(debugDiv);

    console.log("TG:", tg.initDataUnsafe);

    function getTelegramUserId() {
        // 1. Сначала ищем ID в нашей ссылке (100% надежно)
        const urlParams = new URLSearchParams(window.location.search);
        const userIdFromUrl = urlParams.get('user_id');

        if (userIdFromUrl) {
            return parseInt(userIdFromUrl, 10); // Возвращаем как число
        }

        // 2. Если в ссылке нет, пытаемся достать стандартным способом
        if (
            window.Telegram &&
            Telegram.WebApp &&
            Telegram.WebApp.initDataUnsafe &&
            Telegram.WebApp.initDataUnsafe.user
        ) {
            return Telegram.WebApp.initDataUnsafe.user.id;
        }

        return null;
    }

    // Все экраны
    const step0 = document.getElementById('step-0');
    const step1 = document.getElementById('step-1');
    const step2 = document.getElementById('step-2');
    const step3 = document.getElementById('step-3');
    const step4 = document.getElementById('step-4');

    const servicesList = document.getElementById('services-list');
    const mastersList = document.getElementById('masters-list');
    const timeSlotsList = document.getElementById('time-slots-list');
    const datePicker = document.getElementById('date-picker');

    let selectedServiceId = null;
    let selectedMasterId = null;
    let selectedDate = null;
    let selectedTime = null;

    const allWorkSlots = ['10:00','11:00','12:00','13:00','14:00','15:00','16:00','17:00','18:00','19:00'];

    const fetchOptions = {
        headers: {
            'ngrok-skip-browser-warning': 'true'
        }
    };

    // УСЛУГИ
    fetch('/api/services/', fetchOptions)
        .then(res => res.json())
        .then(data => {
            data.forEach(service => {
                const btn = document.createElement('button');
                btn.innerHTML = `<i class="fa-solid fa-hand-scissors"></i> ${service.name}`;
                btn.className = 'action-btn';

                btn.addEventListener('click', function() {
                    selectedServiceId = service.id;
                    step0.style.display = 'none';
                    step1.style.display = 'block';
                });

                servicesList.appendChild(btn);
            });
        });

    // МАСТЕРА
    fetch('/api/masters/', fetchOptions)
        .then(res => res.json())
        .then(data => {
            data.forEach(master => {
                const btn = document.createElement('button');
                btn.innerHTML = `<i class="fa-solid fa-star"></i> ${master.name}`;
                btn.className = 'master-btn';

                btn.addEventListener('click', function() {
                    selectedMasterId = master.id;
                    document.getElementById('selected-master-title').textContent = 'Мастер: ' + master.name;
                    step1.style.display = 'none';
                    step2.style.display = 'block';
                });

                mastersList.appendChild(btn);
            });
        });

    // ДАТА → ВРЕМЯ
    document.getElementById('btn-next').addEventListener('click', function() {

        selectedDate = datePicker.value;

        if (!selectedDate) {
            tg.showAlert("Выберите дату");
            return;
        }

        step2.style.display = 'none';
        step3.style.display = 'block';

        timeSlotsList.innerHTML = '';

        fetch(`/get-booked-slots/?master_id=${selectedMasterId}&date=${selectedDate}`, fetchOptions)
            .then(res => res.json())
            .then(data => {

                if (data.day_off) {
                    timeSlotsList.innerHTML = '<p>Мастер отдыхает</p>';
                    return;
                }

                const bookedSlots = (data.booked || []).map(t => t.substring(0,5));

                allWorkSlots.forEach(slot => {
                    const btn = document.createElement('button');
                    btn.className = 'time-btn';

                    if (bookedSlots.includes(slot)) {
                        btn.innerHTML = `<i class="fa-solid fa-ban"></i> ${slot} (занято)`;
                        btn.disabled = true;
                    } else {
                        btn.innerHTML = `<i class="fa-regular fa-clock"></i> ${slot}`;
                        btn.addEventListener('click', function() {
                            selectedTime = slot;
                            step3.style.display = 'none';
                            step4.style.display = 'block';
                        });
                    }

                    timeSlotsList.appendChild(btn);
                });

            });
    });

    // НАЗАД
    document.getElementById('btn-back-to-services').onclick = () => {
        step1.style.display = 'none';
        step0.style.display = 'block';
    };

    document.getElementById('btn-back-to-masters').onclick = () => {
        step2.style.display = 'none';
        step1.style.display = 'block';
    };

    document.getElementById('btn-back-to-date').onclick = () => {
        step3.style.display = 'none';
        step2.style.display = 'block';
    };

    document.getElementById('btn-back-to-time').onclick = () => {
        step4.style.display = 'none';
        step3.style.display = 'block';
    };

    // ОТПРАВКА
    const btnSubmit = document.getElementById('btn-submit');

    btnSubmit.addEventListener('click', function() {

        const clientName = document.getElementById('client-name').value;
        const clientPhone = document.getElementById('client-phone').value;

        if (!clientName || !clientPhone) {
            tg.showAlert("Введите имя и телефон");
            return;
        }

        // 🔥 ВЫРЕЗАЕМ ID ИЗ ССЫЛКИ ГРУБОЙ СИЛОЙ (РЕГУЛЯРКОЙ)
        let finalUserId = null;
        const urlMatch = window.location.href.match(/user_id=(\d+)/);
        if (urlMatch) {
            finalUserId = parseInt(urlMatch[1], 10);
        } else if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
            finalUserId = tg.initDataUnsafe.user.id;
        }

        console.log("ОТПРАВЛЯЕМ ID:", finalUserId);

        const data = {
            client_name: clientName,
            phone: clientPhone,
            master: selectedMasterId,
            service: selectedServiceId,
            date: selectedDate,
            time: selectedTime,
            telegram_chat_id: finalUserId
        };

        btnSubmit.disabled = true;
        btnSubmit.innerText = "Отправка...";

        fetch('/api/appointment/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(data)
        })
        .then(res => {
            if (res.status === 201) {

                if (tgUserId) {
                    tg.showAlert("✅ Запись создана!", () => tg.close());
                } else {
                    alert("Запись создана (без Telegram)");
                    location.reload();
                }

            } else {
                tg.showAlert("Ошибка записи");
                btnSubmit.disabled = false;
                btnSubmit.innerText = "Подтвердить";
            }
        })
        .catch(err => {
            console.error(err);
            alert("Ошибка сети");
            btnSubmit.disabled = false;
            btnSubmit.innerText = "Подтвердить";
        });

    });

});