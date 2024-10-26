async function showBanner() {
    // Check if mail is sent to a specific address.
    if (!document.body.textContent.includes("tickets@scheinbar.de")) {
        return;
    }

    let bannerDetails = await browser.runtime.sendMessage({
        command: "analyzeMail",
    });

    // Get the details back from the formerly serialized content.
    const { text } = bannerDetails;
    let details = bannerDetails;

    // Create the banner element itself.
    const banner = document.createElement("div");
    banner.className = "thunderbirdMessageDisplayActionExample";

    // Create the banner text element.
    const bannerText = document.createElement("div");
    bannerText.className = "thunderbirdMessageDisplayActionExample_Text";
    // set html content
    bannerText.innerHTML = text;

    // Create a button to display it in the banner.
    const markUnreadButton = document.createElement("button");
    markUnreadButton.innerText = "Antworten";
    markUnreadButton.addEventListener("click", async () => {
        // Add the button event handler to send the command to the
        // background script.
        browser.runtime.sendMessage({
            command: "openReplyMail",
            details: details
        });
    });

    // Add text and button to the banner.
    banner.appendChild(bannerText);
    banner.appendChild(markUnreadButton);

    // Insert it as the very first element in the message.
    document.body.insertBefore(banner, document.body.firstChild);
};

showBanner();
