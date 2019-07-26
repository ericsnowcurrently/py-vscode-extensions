import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {{
    try {{
        activateUnsafe(context);
    }} catch (exc) {{
        notifyUser('Extension activation failed, run the \'Developer: Toggle Developer Tools\' command for more information.');
        console.log(`ERROR: extension activation failed (${{exc}})`);
        throw ex;  // re-raise
    }}
}}

export function deactivate() {{
    // For now do nothing.
}}

function activateUnsafe(context: ExtensionContext) {{
    // Use the console to output diagnostic information (console.log) and errors (console.error)
    // This line of code will only be executed once when your extension is activated
    console.log('Congratulations, your extension "{{name}}" is now active!');

    // Display a message box to the user
    vscode.window.showInformationMessage('Hello World!');
}}

function notifyUser(msg: string) {{
    try {{
        vscode.window.showErrorMessage(msg);
    }} catch (ex) {{
        // ignore
    }}
}}
