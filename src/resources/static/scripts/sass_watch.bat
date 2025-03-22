@echo off

REM ========================================
REM Script to compile SCSS files to CSS files with watch mode
REM ========================================

REM Make sure sass is installed. It can be installed with `npm install -g sass`
sass --watch ../css/:../css
