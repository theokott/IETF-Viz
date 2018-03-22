function init(evt)
{
    if ( window.svgDocument == null )
    {
        svgDocument = evt.target.ownerDocument;
    }
    tooltip_bg = svgDocument.getElementById('tooltip_bg');
    title = svgDocument.getElementById('title');
    rfc = svgDocument.getElementById('rfc');
    draft = svgDocument.getElementById('draft');
    abstract = svgDocument.getElementById('abstract');
    group = svgDocument.getElementById('group');
    area = svgDocument.getElementById('area');
    creation = svgDocument.getElementById('creation');
    publish = svgDocument.getElementById('publish');
    console.log("INIT RUN");
}

function ShowTooltip(evt, mouseovertext)
{
    console.log('show tooltip called!');
    var splitText = mouseovertext.split("***");
    var maxLength = 0;
    console.log("split: " + splitText);
    for (i = 0; i < splitText.length; i++){
        if (splitText[i].length > maxLength) {
            maxLength = splitText[i].length;
        }
    }
    console.log("max length: ", maxLength);
    title.setAttributeNS(null,"x",evt.clientX+11);
    title.setAttributeNS(null,"y",evt.clientY+25);
    title.setAttributeNS(null,"visibility","visible");
    rfc.setAttributeNS(null,"x",evt.clientX+11);
    rfc.setAttributeNS(null,"y",evt.clientY+45);
    rfc.setAttributeNS(null,"visibility","visible");
    draft.setAttributeNS(null,"x",evt.clientX+11);
    draft.setAttributeNS(null,"y",evt.clientY+65);
    draft.setAttributeNS(null,"visibility","visible");
    abstract.setAttributeNS(null,"x",evt.clientX+11);
    abstract.setAttributeNS(null,"y",evt.clientY+85);
    abstract.setAttributeNS(null,"visibility","visible");
    group.setAttributeNS(null,"x",evt.clientX+11);
    group.setAttributeNS(null,"y",evt.clientY+105);
    group.setAttributeNS(null,"visibility","visible");
    area.setAttributeNS(null,"x",evt.clientX+11);
    area.setAttributeNS(null,"y",evt.clientY+125);
    area.setAttributeNS(null,"visibility","visible");
    creation.setAttributeNS(null,"x",evt.clientX+11);
    creation.setAttributeNS(null,"y",evt.clientY+145);
    creation.setAttributeNS(null,"visibility","visible");
    publish.setAttributeNS(null,"x",evt.clientX+11);
    publish.setAttributeNS(null,"y",evt.clientY+165);
    publish.setAttributeNS(null,"visibility","visible");
    title.firstChild.data = splitText[0];
    rfc.firstChild.data = splitText[1];
    draft.firstChild.data = splitText[2];
    abstract.firstChild.data = splitText[3];
    group.firstChild.data = splitText[4];
    area.firstChild.data = splitText[5];
    creation.firstChild.data = splitText[6];
    publish.firstChild.data = splitText[7];
    tooltip_bg.setAttributeNS(null,"x",evt.clientX+8);
    tooltip_bg.setAttributeNS(null,"y",evt.clientY+10);
    tooltip_bg.setAttributeNS(null,"width", maxLength * 8);
    tooltip_bg.setAttributeNS(null,"height", 165);
    tooltip_bg.setAttributeNS(null,"visibility","visible");
}
function HideTooltip()
{
    tooltip_bg.setAttributeNS(null,"visibility","hidden");
    title.setAttributeNS(null,"visibility","hidden");
    rfc.setAttributeNS(null,"visibility","hidden");
    draft.setAttributeNS(null,"visibility","hidden");
    abstract.setAttributeNS(null,"visibility","hidden");
    group.setAttributeNS(null,"visibility","hidden");
    area.setAttributeNS(null,"visibility","hidden");
    creation.setAttributeNS(null,"visibility","hidden");
    publish.setAttributeNS(null,"visibility","hidden");
}