#!/data/data/com.termux/files/usr/bin/bash
echo "======================================================"
echo " АВТОМАТИЧЕСКАЯ ОТПРАВКА ПРОЕКТА КУБКОД-125 НА GITHUB"
echo "======================================================"
pkg install -y git
read -p "Введите ваш логин GitHub: " GH_USER
read -p "Введите название нового репозитория (например, kubkod-apk): " GH_REPO
read -p "Введите ваш GitHub Token (PAT): " GH_TOKEN

git init
git branch -M main
git config user.name "$GH_USER"
git config user.email "$GH_USER@users.noreply.github.com"
git add .
git commit -m "KUBKOD-125 Real-Time Sensor Filter APK"
git remote remove origin 2>/dev/null
git remote add origin "https://$GH_USER:$GH_TOKEN@github.com/$GH_USER/$GH_REPO.git"
git push -u origin main --force

echo "======================================================"
echo " ГОТОВО! Откройте на телефоне ссылку:"
echo " https://github.com/$GH_USER/$GH_REPO/actions"
echo "Через 2 минуты скачайте готовый KUBKOD-125-Sensor-APK!"
echo "======================================================"
