function init(evt)
{
    if ( window.svgDocument == null )
    {
        svgDocument = evt.target.ownerDocument;
    }
    tooltip_bg = svgDocument.getElementById('tooltip_bg');
    title = svgDocument.getElementById('title');
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
    console.log('show tooltip called!')
    var splitText = mouseovertext.split("   ");
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
    draft.setAttributeNS(null,"x",evt.clientX+11);
    draft.setAttributeNS(null,"y",evt.clientY+45);
    draft.setAttributeNS(null,"visibility","visible");
    abstract.setAttributeNS(null,"x",evt.clientX+11);
    abstract.setAttributeNS(null,"y",evt.clientY+65);
    abstract.setAttributeNS(null,"visibility","visible");
    group.setAttributeNS(null,"x",evt.clientX+11);
    group.setAttributeNS(null,"y",evt.clientY+85);
    group.setAttributeNS(null,"visibility","visible");
    area.setAttributeNS(null,"x",evt.clientX+11);
    area.setAttributeNS(null,"y",evt.clientY+105);
    area.setAttributeNS(null,"visibility","visible");
    creation.setAttributeNS(null,"x",evt.clientX+11);
    creation.setAttributeNS(null,"y",evt.clientY+125);
    creation.setAttributeNS(null,"visibility","visible");
    publish.setAttributeNS(null,"x",evt.clientX+11);
    publish.setAttributeNS(null,"y",evt.clientY+145);
    publish.setAttributeNS(null,"visibility","visible");
    title.firstChild.data = splitText[0];
    draft.firstChild.data = splitText[1];
    abstract.firstChild.data = splitText[2];
    group.firstChild.data = splitText[3];
    area.firstChild.data = splitText[4];
    creation.firstChild.data = splitText[5];
    publish.firstChild.data = splitText[6];
    tooltip_bg.setAttributeNS(null,"x",evt.clientX+8);
    tooltip_bg.setAttributeNS(null,"y",evt.clientY+10);
    tooltip_bg.setAttributeNS(null,"width", maxLength * 8);
    tooltip_bg.setAttributeNS(null,"height", 145);
    tooltip_bg.setAttributeNS(null,"visibility","visible");
}
function HideTooltip()
{
    tooltip_bg.setAttributeNS(null,"visibility","hidden");
    title.setAttributeNS(null,"visibility","hidden");
    draft.setAttributeNS(null,"visibility","hidden");
    abstract.setAttributeNS(null,"visibility","hidden");
    group.setAttributeNS(null,"visibility","hidden");
    area.setAttributeNS(null,"visibility","hidden");
    creation.setAttributeNS(null,"visibility","hidden");
    publish.setAttributeNS(null,"visibility","hidden");
}