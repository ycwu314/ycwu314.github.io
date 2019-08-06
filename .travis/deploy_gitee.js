
var webdriver = require('selenium-webdriver'),
    By = webdriver.By,
    until = webdriver.until,
    Key = webdriver.Key;

var chrome = require('selenium-webdriver/chrome');
var options = new chrome.Options();
options.addArguments("--headless");
options.addArguments("--no-sandbox");
options.addArguments("--disable-gpu");
// chrome exe路径
// chrome driver要放在$PATH
options.setChromeBinaryPath("/usr/bin/google-chrome-stable");

(async function example() {
    let driver = await new webdriver.Builder().forBrowser('chrome').setChromeOptions(options).build();
    try {
        await driver.get('https://gitee.com/login');
        await driver.findElement({ id: 'user_login' }).sendKeys(process.env.GITEE_USER);
        await driver.findElement({ id: 'user_password' }).sendKeys(process.env.GITEE_PWD, Key.ENTER);
        await driver.sleep(3000);
        await driver.get('https://gitee.com/ycwu314/ycwu314/pages');
        await driver.sleep(3000);
        await driver.findElement(By.className('update_deploy')).click();
        await driver.sleep(3000);
        await driver.switchTo().alert().accept();

    } finally {
        await driver.quit();
    }
})();
