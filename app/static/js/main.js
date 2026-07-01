// =============================
// HORLOGE EN TEMPS RÉEL
// =============================

function mettreAJourHeure() {

    const maintenant = new Date();

    const date = maintenant.toLocaleDateString(
        "fr-FR",
        {
            weekday: "long",
            year: "numeric",
            month: "long",
            day: "numeric"
        }
    );

    const heure = maintenant.toLocaleTimeString(
        "fr-FR"
    );

    const dateElement =
        document.getElementById("date");

    const heureElement =
        document.getElementById("heure");

    if(dateElement){

        dateElement.innerHTML = "📅 " + date;

    }

    if(heureElement){

        heureElement.innerHTML = "🕒 " + heure;

    }

}

mettreAJourHeure();

setInterval(
    mettreAJourHeure,
    1000
);

// =============================
// ANIMATION DES CARTES
// =============================

window.addEventListener(
    "load",
    function(){

        const cartes =
            document.querySelectorAll(".card");

        cartes.forEach(function(card,index){

            card.style.opacity = "0";

            card.style.transform =
                "translateY(40px)";

            setTimeout(function(){

                card.style.transition =
                    "0.5s";

                card.style.opacity = "1";

                card.style.transform =
                    "translateY(0px)";

            },index*120);

        });

    }
);

// =============================
// CONFIRMATION SUPPRESSION
// =============================

const boutonsSupprimer =
    document.querySelectorAll(".delete");

boutonsSupprimer.forEach(function(btn){

    btn.addEventListener(
        "click",
        function(e){

            if(
                !confirm(
                    "Voulez-vous vraiment supprimer cet élément ?"
                )
            ){

                e.preventDefault();

            }

        }
    );

});
