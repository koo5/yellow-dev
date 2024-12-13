<div id="app-container"></div>

<script>
    import { onMount } from "svelte";
    import variant from "@jitl/quickjs-singlefile-browser-debug-sync";
    import { newQuickJSWASMModuleFromVariant } from "quickjs-emscripten-core";

    onMount(async () => {
        const QuickJS = await newQuickJSWASMModuleFromVariant(variant);
        console.log("QuickJS", QuickJS);

        const context = QuickJS.newContext();
        console.log("context", context);

        // We'll store references to DOM elements by numeric handles.
        const elementMap = new Map();
        let nextHandle = 1;

        // The root element for all DOM manipulation
        const rootDiv = document.getElementById('app-container');
        const rootHandle = 0;
        elementMap.set(rootHandle, rootDiv);

        function storeElementAndGetHandle(elem) {
            const handle = nextHandle++;
            elementMap.set(handle, elem);
            return handle;
        }

        function getElementFromHandle(handle) {
            return elementMap.get(handle);
        }

        // Define our DOM manipulation methods
        const bridgeMethods = {
            createElement: (tagName) => {
                console.log("createElement", tagName);
                const element = document.createElement(tagName);
                return storeElementAndGetHandle(element);
            },
            appendChild: (parentHandle, childHandle) => {
                const parent = getElementFromHandle(parentHandle);
                const child = getElementFromHandle(childHandle);
                if (parent && child) {
                    parent.appendChild(child);
                } else {
                    throw new Error("appendChild: invalid handles");
                }
            },
            setTextContent: (handle, text) => {
                const elem = getElementFromHandle(handle);
                if (elem) {
                    elem.textContent = String(text);
                } else {
                    throw new Error("setTextContent: invalid handle");
                }
            },
            setAttribute: (handle, name, value) => {
                // Disallow event attributes as a simple security measure
                if (name.startsWith('on')) {
                    throw new Error(`setAttribute: event attributes not allowed (${name})`);
                }
                const elem = getElementFromHandle(handle);
                if (elem) {
                    elem.setAttribute(name, String(value));
                } else {
                    throw new Error("setAttribute: invalid handle");
                }
            },
            clearChildren: (handle) => {
                const elem = getElementFromHandle(handle);
                if (elem) {
                    while (elem.firstChild) {
                        elem.removeChild(elem.firstChild);
                    }
                } else {
                    throw new Error("clearChildren: invalid handle");
                }
            },
            remove: (handle) => {
                const elem = getElementFromHandle(handle);
                if (elem && elem.parentNode) {
                    elem.parentNode.removeChild(elem);
                } else {
                    throw new Error("remove: invalid handle or element has no parent");
                }
            }
        };

        // Wrap a host function for QuickJS
        function wrapHostFunction(context, name, fn) {
            return context.newFunction(name, (...args) => {
                try {
                    return fn(context, ...args);
                } catch (err) {
                    console.error("Error in wrapped function:", err);
                    throw err;
                }
            });
        }

        // Create JS objects `window` and `document` inside the QuickJS context
        const windowObj = context.unwrapResult(context.evalCode(`({})`));
        const documentObj = context.unwrapResult(context.evalCode(`({})`));

        // Add the bridgeMethods to `document`
        for (const [name, fn] of Object.entries(bridgeMethods)) {
            const wrapped = wrapHostFunction(context, name, (ctx, ...args) => {
                const jsArgs = args.map(arg => {
                    // Convert QuickJS values to JS primitives if needed
                    if (typeof arg === 'object' && 'toString' in arg) {
                        return arg.toString();
                    }
                    return arg;
                });
                try {
                    const result = fn(...jsArgs);
                    return result;
                } catch (err) {
                    console.error("document method error:", err);
                    throw err;
                }
            });
            context.setProp(documentObj, name, wrapped);
            wrapped.dispose();
        }

        // Link window and document
        context.setProp(windowObj, 'document', documentObj);
        context.setProp(context.global, 'window', windowObj);
        context.setProp(context.global, 'document', documentObj);

        documentObj.dispose();
        windowObj.dispose();

        // Example user code to run in the sandboxed environment
        const userCode = `
            const root = 0; // root div handle
            const title = document.createElement('h1');
            document.setTextContent(title, 'Hello from the sandbox!');
            document.appendChild(root, title);

            const para = document.createElement('p');
            document.setTextContent(para, 'This is a paragraph created in a sandboxed JS environment.');
            document.appendChild(root, para);

            // The following would throw an error if uncommented
            // document.setAttribute(para, 'onmouseover', 'alert("hacked!")');
        `;

        const result = context.evalCode(userCode);
        if (result.error) {
            console.error('Error in user code:', context.dump(result.error));
            result.error.dispose();
        } else {
            result.value.dispose();
        }

        context.dispose();
    });
</script>
