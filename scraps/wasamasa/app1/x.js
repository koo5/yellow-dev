function shadowRootTest() {

    const shadowTestElement = document.getElementById('shadowtest');

    if (shadowTestElement) {
        shadowTestElement.appendChild(moduleContainer);
    } else {
        console.error('Element with id "shadowtest" not found.');
    }

    const moduleContainer = document.createElement('div');
    const shadowRoot = moduleContainer.attachShadow({mode: 'closed'});
    shadowRoot.appendChild(document.createElement('pre'));

}

function test() {
    document.write("Hello World!Hello World!Hello World!Hello World!Hello World!Hello World!Hello World!Hello World!Hello World!Hello World!Hello World!Hello World!Hello World!Hello World!Hello World!Hello World!Hello World!");
}
