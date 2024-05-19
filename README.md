Рекомендуется разворачивать Ubuntu 22.04
Наличие ssh на машинах 

В файле vars.yml указать своих пользователей и IP. 
!!!В файле inventory.yml указать свой пароль пользователя ansible!!!

Для запуска playbook'а используется команда:
ansible-playbook playbook_tg_bot.yml -e @vars.yml
