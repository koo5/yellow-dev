<div id="app-container"></div>

<script>
    //import { getQuickJS } from "quickjs-emscripten"
    import {onMount} from "svelte";


    import variant from "@jitl/quickjs-singlefile-browser-debug-sync"
    import {newQuickJSWASMModuleFromVariant} from "quickjs-emscripten-core"

    onMount(async () => {

        const QuickJS = await newQuickJSWASMModuleFromVariant(variant);


        console.log("QuickJS", QuickJS)

        const context = QuickJS.newContext();
        console.log("context", context)

        // We'll store references to DOM elements by numeric handles.
        const elementMap = new Map();
        let nextHandle = 1;

        // The root element for all DOM manipulation (the "sandboxed DOM")
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

        // Define our DOM manipulation methods.
        // These methods should sanitize and validate their inputs if needed.
        const bridgeMethods = {
            createElement: (tagName) => {
                console.log("createElement", tagName)
                console.log(tagName)
                // Sanitize tagName if desired, e.g. ensure it's a known HTML tag
                // For simplicity, assume tagName is safe
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
                // Possibly sanitize text to ensure no dangerous HTML injection
                const elem = getElementFromHandle(handle);
                if (elem) {
                    elem.textContent = String(text);
                } else {
                    throw new Error("setTextContent: invalid handle");
                }
            },
            setAttribute: (handle, name, value) => {
                // Sanitize attribute name and value if desired
                // For example, disallow "on*" attributes to prevent event handler injection
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


        // Manually wrap a host function for QuickJS
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

        // Wrap these methods so they can be called from QuickJS
        // We'll create an object `DOMBridge` in the QuickJS environment.
        const domBridge = context.unwrapResult(context.evalCode(`({})`));

        for (const [name, fn] of Object.entries(bridgeMethods)) {

// Use the manual wrapper instead of context.wrapHostFunction
            const wrapped = wrapHostFunction(context, name, (ctx, ...args) => {
                // Convert args from QuickJS values to JS values
                const jsArgs = args.map(arg => {
                    if (typeof arg === 'object' && 'toString' in arg) {
                        // If arg is a QuickJS string or number, call toString
                        return arg.toString();
                    }
                    return arg; // For numbers and other primitives
                });
                try {
                    const result = fn(...jsArgs);
                    return result;
                } catch (err) {
                    console.error("DOMBridge error:", err);
                    throw err; // Rethrow to report error to QuickJS side
                }
            });
            context.setProp(domBridge, name, wrapped);
            wrapped.dispose();
        }

        context.setProp(context.global, 'DOMBridge', domBridge);
        domBridge.dispose();

        // Example user code to run in the sandboxed environment
        const userCode = `
        // We know handle 0 is the root div
        const root = 0;
        const title = DOMBridge.createElement('h1');
        DOMBridge.setTextContent(title, 'Hello from the sandbox!');
        DOMBridge.appendChild(root, title);

        const para = DOMBridge.createElement('p');
        DOMBridge.setTextContent(para, 'This is a paragraph created in a sandboxed JS environment.');
        DOMBridge.appendChild(root, para);

        // Attempt to set an unsafe attribute - this should cause an error if we disallow 'on*'
        // DOMBridge.setAttribute(para, 'onmouseover', 'alert("hacked!")'); // Uncomment to test security
      `;

        const result = context.evalCode(userCode);
        if (result.error) {
            console.error('Error in user code:', context.dump(result.error));
            result.error.dispose();
        } else {
            // If no error, we can dispose the returned value
            result.value.dispose();
        }

        context.dispose();
    });

</script>
