document.addEventListener("DOMContentLoaded", function () {

  //****************************
  // Theme Onload Toast
  //****************************
  window.addEventListener("load", () => {
    let myAlert = document.querySelectorAll('.toast')[0];
    if (myAlert) {
      let bsAlert = new bootstrap.Toast(myAlert);
      bsAlert.show();
    }
  })


})