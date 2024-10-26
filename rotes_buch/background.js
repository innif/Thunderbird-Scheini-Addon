// Import all functions defined in the messageTools module.
import * as messageTools from '/modules/messageTools.mjs';

let base64Credentials = btoa(`${username}:${password}`);

// Add a listener for the onNewMailReceived events.
messenger.messages.onNewMailReceived.addListener(async (folder, messages) => {
    let { messageLog } = await messenger.storage.local.get({ messageLog: [] });

    for await (let message of messageTools.iterateMessagePages(messages)) {
        messageLog.push({
            folder: folder.name,
            time: Date.now(),
            message: message
        })
    }

    await messenger.storage.local.set({ messageLog });
})

// Create the menu entries.
let menu_id = await messenger.menus.create({
    title: "Show received email",
    contexts: [
        "browser_action",
        "tools_menu"
    ],
});

// Register a listener for the menus.onClicked event.
await messenger.menus.onClicked.addListener(async (info, tab) => {
    if (info.menuItemId == menu_id) {
        // Our menu entry was clicked
        let { messageLog } = await messenger.storage.local.get({ messageLog: [] });

        let now = Date.now();
        let last24h = messageLog.filter(e => (now - e.time) < 24 * 60 * 1000);

        for (let entry of last24h) {
            messenger.notifications.create({
                "type": "basic",
                "iconUrl": "images/internet.png",
                "title": `${entry.folder}: ${entry.message.author}`,
                "message": entry.message.subject
            });
        }
    }
});

// Register the message display script for all newly opened message tabs.
messenger.messageDisplayScripts.register({
    js: [{ file: "messageDisplay/message-content-script.js" }],
    css: [{ file: "messageDisplay/message-content-styles.css" }],
});

// Inject script and CSS in all already open message tabs.
let openTabs = await messenger.tabs.query();
let messageTabs = openTabs.filter(
    tab => ["mail", "messageDisplay"].includes(tab.type)
);
for (let messageTab of messageTabs) {
    browser.tabs.executeScript(messageTab.id, {
        file: "messageDisplay/message-content-script.js"
    })
    browser.tabs.insertCSS(messageTab.id, {
        file: "messageDisplay/message-content-styles.css"
    })
}

/**
 * Add a handler for the communication with other parts of the extension,
 * like our message display script.
 *
 * Note: It is best practice to always define a synchronous listener
 *       function for the runtime.onMessage event.
 *       If defined asynchronously, it will always return a Promise
 *       and therefore answer all messages, even if a different listener
 *       defined elsewhere is supposed to handle these.
 * 
 *       The listener should only return a Promise for messages it is
 *       actually supposed to handle.
 */
messenger.runtime.onMessage.addListener((message, sender, sendResponse) => {
    // Check what type of message we have received and invoke the appropriate
    // handler function.
    if (message && message.hasOwnProperty("command")) {
        return commandHandler(message, sender);
    }
    // Return false if the message was not handled by this listener.
    return false;
});

// The actual (asynchronous) handler for command messages.
async function commandHandler(message, sender) {
    // Get the message currently displayed in the sending tab, abort if
    // that failed.
    const messageHeader = await messenger.messageDisplay.getDisplayedMessage(
        sender.tab.id
    );

    if (!messageHeader) {
        return;
    }

    // get Mail content
    const message_content = await messenger.messages.getFull(messageHeader.id);

    let user = "api";
    let password = "api";

    // Check for known commands.
    console.log("Switch");
    switch (message.command) {
        case "analyzeMail":
            // send to API for analysis
            let analysis = await fetch('https://rotes-buch.scheinbar.de:5001/analyze', {
                method: 'POST',
                body: JSON.stringify({
                    subject: messageHeader.subject,
                    author: messageHeader.author,
                    content: message_content
                }),
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Basic ${base64Credentials}`
                }
            });
            let result = await analysis.json();
            return result;
        case "getBannerDetails":
            // Create the information we want to return to our message display
            // script.
            return { text: `Mail subject is "${messageHeader.subject}"` };
        case "markUnread":
            // Mark the message as unread.
            messenger.messages.update(messageHeader.id, {
                read: false,
            });
            break;
        case "openReplyMail":
            // Open a new tab with a reply to the message.
            try {
                let analysis = await fetch('https://rotes-buch.scheinbar.de:5001/gen_response', {
                    method: 'POST',
                    body: JSON.stringify({
                        subject: messageHeader.subject,
                        author: messageHeader.author,
                        content: message_content,
                        details: message.details
                    }),
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Basic ${base64Credentials}`
                    }
                });

                let result = await analysis.json();

                console.log(result);
                // Beginne die Antwort auf die Nachricht
                let replyWindow = await browser.compose.beginReply(messageHeader.id);
            
                // Warte ein wenig, um sicherzustellen, dass das Antwortfenster bereit ist
                await new Promise(resolve => setTimeout(resolve, 500));
            
                // Setze den gewünschten Inhalt in das Fenster
                let new_content = result.text;
            
                // get current content
                let currentContent = await browser.compose.getComposeDetails(replyWindow.id);
                
                // append current content to the new content
                let content = currentContent.body;

                // if mail is html, add new content after <body> tag
                if (content.includes("<body")) {
                    // insert new content after <body> tag
                    content = content.replace(/<body[^>]*>/, `$&${new_content}`);
                } else {
                    // insert new content at the end of the mail
                    content = new_content + content;
                }

                // Setze den Body-Inhalt in das geöffnete Fenster
                await browser.compose.setComposeDetails(replyWindow.id, {
                  body: content
                });
            
              } catch (error) {
                console.error("Fehler beim Hinzufügen des Inhalts zur Antwort:", error);
              }
          
            break;
    }
}
