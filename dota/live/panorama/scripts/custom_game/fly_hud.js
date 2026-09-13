(function () {
    let selected = -1;
    GameEvents.Subscribe("fly_status", function (event) {
        $("#FlyStatus").text = event.status;
        $("#FlyAction").text = event.action;
        if (event.entity !== selected) {
            GameUI.SelectUnit(event.entity, false);
            selected = event.entity;
        }
    });
})();
