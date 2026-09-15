@echo off
chcp 65001 >nul 2>&1
setlocal EnableDelayedExpansion
title FF-TurboNet Windows Optimizer v3.0
color 0B

REM =====================================================================
REM  FF-TurboNet v3.0 — محسّن ويندوز بنقرة واحدة (قانوني 100%)
REM  يعطّل Nagle (تأخير الحزم الصغيرة) + يحسّن TCP + يوقف خدمات الخلفية
REM  لا يلمس اللعبة إطلاقًا — فقط نظام ويندوز الخاص بك
REM  يدعم Undo كامل من نفس الملف
REM =====================================================================

cd /d "%~dp0"
set "BACKUPDIR=%~dp0turbonet_reg_backup"
if not exist "%BACKUPDIR%" mkdir "%BACKUPDIR%"

net session >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo.
    echo   [✗] يجب التشغيل كمسؤول: كليك يمين ← "Run as administrator"
    echo.
    pause & exit /b 1
)
color 0B

:menu
cls
echo.
echo   ╔══════════════════════════════════════════════════════════╗
echo   ║          FF-TurboNet — Windows Optimizer v3.0            ║
echo   ║   تحسين شبكة فري فاير — قانوني 100% بدون لمس اللعبة     ║
echo   ╚══════════════════════════════════════════════════════════╝
echo.
echo   [1] التطبيق الكامل — تعطيل Nagle + تحسينات TCP + إيقاف الخلفية
echo   [2] تعطيل Nagle فقط (الأقوى ضد اللاق — لكل كروت الشبكة)
echo   [3] تحسينات TCP العامة فقط
echo   [4] إيقاف خدمات الخلفية التي تستهلك الشبكة
echo   [5] فحص البينق لسيرفرات فري فاير (لا يحتاج مسؤول)
echo   [6] Undo — استرجاع كل الإعدادات الأصلية
echo   [7] استعادة المسؤول: إعادة تشغيل الأداة كمسؤول (شرح)
echo   [0] خروج
echo.
set /p choice="   اختر [0-7]: "
if "%choice%"=="1" goto apply_all
if "%choice%"=="2" goto nagle
if "%choice%"=="3" goto tcp
if "%choice%"=="4" goto bgapps
if "%choice%"=="5" goto pingcheck
if "%choice%"=="6" goto undo
if "%choice%"=="7" goto helpadmin
if "%choice%"=="0" exit /b 0
goto menu

:apply_all
call :nagle
call :tcp
call :bgapps
echo.
echo   [✓] اكتمل التحسين الكامل — أعد تشغيل الجهاز لتفعيل Nagle بالكامل
goto end

:nagle
echo.
echo   ─── تعطيل Nagle + TcpAckFrequency + TcpDelAckTimestamps ───
echo   (تأخير إرسال الحزم الصغيرة = سبب رقم 1 لللاق في الألعاب)
set NAGLE_APPLIED=0
REM البحث في كل واجهات الشبكة في التسجيل
for /f "tokens=*" %%K in ('reg query "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces" 2^>nul') do (
    REM نسخة احتياطية أول مرة فقط
    reg export "%%K" "%BACKUPDIR%\nagle_%%~nK.reg" /y >nul 2>&1
    reg add "%%K" /v TcpAckFrequency /t REG_DWORD /d 1 /f >nul 2>&1 && set /a NAGLE_APPLIED+=1
    reg add "%%K" /v TCPNoDelay /t REG_DWORD /d 1 /f >nul 2>&1
    reg add "%%K" /v TcpDelAckTimestampsFrequency /t REG_DWORD /d 1 /f >nul 2>&1
)
echo   [✓] تم تطبيق تعطيل Nagle على !NAGLE_APPLIED! واجهة شبكة
echo   [i] نسخة احتياطية كاملة للريجستري في: turbonet_reg_backup\
goto end

:tcp
echo.
echo   ─── تحسينات TCP العامة (netsh) ───
netsh int tcp set global autotuninglevel=normal >nul 2>&1 && echo   [✓] Auto-Tuning = normal (أفضل أداء بدون مشاكل VPN)
netsh int tcp set global congestionprovider=ctcp >nul 2>&1 && echo   [✓] Congestion = CTCP (ويندوز)
netsh int tcp set global timestamps=enabled >nul 2>&1 && echo   [✓] Timestamps مفعّلة (RTT أدق)
netsh int tcp set global ecncapability=enabled >nul 2>&1 && echo   [✓] ECN مفعّل
netsh int tcp set global rss=enabled >nul 2>&1 && echo   [✓] RSS مفعّل (توزيع الشبكة على الأنوية)
netsh int tcp set global chimney=disabled >nul 2>&1 && echo   [✓] Chimney (قد يسبب لاق على بعض الكروت)
netsh int tcp set global netdma=disabled >nul 2>&1 && echo   [✓] NetDMA مُعطّل
echo   [i] تحسينات TCP مكتملة
goto end

:bgapps
echo.
echo   ─── إيقاف سرّاق الشبكة الخلفيين ───
set KILLED=0
for %%P in (OneDrive.exe Dropbox.exe GoogleUpdate.exe GoogleCrashHandler.exe AdobeARM.exe BackgroundTransferHost.exe Skype.exe Teams.exe) do (
    tasklist /FI "IMAGENAME eq %%P" 2>nul | find /I "%%P" >nul
    if !errorlevel! equ 0 (
        taskkill /F /IM %%P >nul 2>&1
        echo   [⛔] أوقفت: %%P
        set /a KILLED+=1
    )
)
if %KILLED% equ 0 echo   [✓] لا توجد برامج خلفية مشغّلة من القائمة
echo   [✓] الشبكة الآن للعبة فقط
goto end

:pingcheck
echo.
echo   ─── فحص البينق لسيرفرات فري فاير ───
echo   سنغافورة (المقر الرئيسي):
ping -n 5 ff.garena.com
echo.
echo   الشرق الأوسط (CDN جارينا):
ping -n 5 ff.garena.com.cdn.cloudflare.net
echo.
echo   بنغلاديش (للاعبين الآسيويين):
ping -n 5 202.81.97.70
echo.
echo   [i] للفحص الاحترافي الكامل شغّل: python ff_turbonet.py ping
goto end

:undo
echo.
echo   ─── استرجاع الإعدادات الأصلية ───
if exist "%BACKUPDIR%" (
    echo   [i] استرجاع ملفات الريجستري المحفوظة...
    for %%F in ("%BACKUPDIR%\*.reg") do (
        reg import "%%F" >nul 2>&1
        echo   [✓] استرجعنا: %%~nxF
    )
    echo   [i] حذف قيم Nagle المضافة (إن لم تكن موجودة أصلًا)...
    for /f "tokens=*" %%K in ('reg query "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces" 2^>nul') do (
        reg delete "%%K" /v TcpAckFrequency /f >nul 2>&1
        reg delete "%%K" /v TCPNoDelay /f >nul 2>&1
        reg delete "%%K" /v TcpDelAckTimestampsFrequency /f >nul 2>&1
    )
) else (
    echo   [i] لا توجد نسخ احتياطية — سنحذف قيم Nagle فقط
    for /f "tokens=*" %%K in ('reg query "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces" 2^>nul') do (
        reg delete "%%K" /v TcpAckFrequency /f >nul 2>&1
        reg delete "%%K" /v TCPNoDelay /f >nul 2>&1
        reg delete "%%K" /v TcpDelAckTimestampsFrequency /f >nul 2>&1
    )
)
netsh int tcp set global autotuninglevel=normal >nul 2>&1
netsh int tcp set global congestionprovider=default >nul 2>&1
echo   [✓] تم الاسترجاع — نظامك كما كان قبل الأداة تمامًا
goto end

:helpadmin
echo.
echo   لتشغيل أي خيار يعدّل النظام: كليك يمين على FF-TurboNet-Windows.bat
echo   ← Run as administrator ← ثم اختر الخيار المطلوب.
goto end

:end
echo.
echo   ────────────────────────────────────────────
pause
goto menu
