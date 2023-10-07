# Getting Started

## Setting up and Usage

And now I will tell you a story of how to setup your new LoveCube.

### Step 1: Setup your account

1. Go to [LoveCube's website](https://frank20a.pythonanywhere.com/register) and create an account.
2. Create an access key for your new LoveCube [here](https://frank20a.pythonanywhere.com/authkeys).
    1. First, you need to find your LoveCube's ID. Read [here](#how-to-find-your-lovecubes-id) how to do that.
    2. On the Authkeys page, select *New device* on the dropdown on the first line. If you have already registered your LoveCube, select it from the dropdown and you can create additional keys for it.
    3. If you are creating a new device, enter your LoveCube's ID in the text box.
    4. Click on *Create key* and you will see your new access key.
    5. The page will refresh and you will find a new access key for your device on the list. Click on the *Copy Key* button to copy it to your clipboard.
3. Got to the [Devices](https://frank20a.pythonanywhere.com/devices) to confirm your device has been registered and give it a nickname if you want to.

### Step 2: Setup your LoveCube

1. Connect your LoveCube to power and let it boot up.
2. If your LoveCube is new, it will create a WiFi network called `LoveCube-XXXXXX` where `XXXXXX` is your LoveCube's ID. Connect to it. If it doesn't, you will need to [reset it](#resetting-your-lovecube).
3. Open a browser and go to [http://setup.lovecube.com](http://setup.lovecube.com). Enter your WiFi network's name and password. Also enter the access key you created in the previous step.
4. Click on *Save* and wait for your LoveCube to connect to the internet. This may take a few minutes. You may close the browser window.
5. Go to the [Devices](https://frank20a.pythonanywhere.com/devices) page and confirm your LoveCube is connected. The *Last Ping* column should show a recent date and time and be green. Here, you can also see the charging status of your LoveCube.

### Step 3: Create a Pair

1. Go to the [Pairs](https://frank20a.pythonanywhere.com/pairs). On the right side, you can see a list of the Pair Requests you have **made**. To create a new one, ask your partner for their LoveCube's ID and enter it in the *Device ID* text box. Then click on *Request*.
2. On the left side, you can see a list of the Pair Requests you have **received**, including who sent it and what device of yours they want to control. You can accept or decline them from the appropriate buttons.
3. After your partner accepts your request, it will show as **ACCEPTED** in the *My Pairs* list. You can now start nodding.
4. Go to the [Devices](https://frank20a.pythonanywhere.com/devices) page. Here you can configure what your LoveCube does when you press its buttons. Button A and B can be configured independently. You have 3 options for each button:
    1. Target device: Select the device you want to control when you press the button. A list of the your partners accepted Pair Requests will be shown.
    2. Action: Select what their device's lights will do when you press the button.
    3. Duration: Select how long the action will last.
5. Press *Save Edit* to save your changes.

### Step 4: Start Nodding

You are ready to use your device! Give it a try and see what happens. Each device checks for new commands every 10 seconds, so it may take a few seconds for your partner's device to react.

## How to find your LoveCube's ID

There are three ways to find your LoveCube's ID. The first two only work if you have a new LoveCube or you have just [reseted it](#resetting-your-lovecube). The third one works always.

### LoveCube access point name

1. Power up your NEW or RESETED LoveCube and wait for it to create a WiFi network.
2. Check the list of available networks on your computer or smartphone. You will find one with the name `LoveCube-XXXXXX` where `XXXXXX` is your LoveCube's ID. It will be a 5 or 6 digit code containing only numbers and letters.

### LoveCube setup page

1. Repeat the steps of the previous method.
2. Connect to the `LoveCube-XXXXXX` network.
3. Open a browser and go to [http://setup.lovecube.com](http://setup.lovecube.com). You will see the LoveCube's ID at the bottom-left of the page.

### LoveCube setup tool

1. Connect your LoveCube to your computer using a USB cable.
2. Open a terminal in the `lovecube` folder.
3. Run the setup tool using `python3 ./tools/setup.py`.
4. Select the serial port of your LoveCube.
5. Select option 2 to get the LoveCube's ID.

## Resetting your LoveCube

This is helpful when you want to change Wi-Fi networks or when you want to give your LoveCube to someone else.

1. Connect your LoveCube to your computer using a USB cable.
2. Open a terminal in the `lovecube` folder.
3. Run the setup tool using `python3 ./tools/setup.py`.
4. Select the serial port of your LoveCube.
5. Select option 1 to reset your LoveCube.