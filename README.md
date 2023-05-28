# Odoo-Hotel-Management <sub><i>Odoo 15</i></sub>
Addon do Odoo 15 odpowiedzialny za tworzenie i zarządanie: klientami, rezerwacjami, pokojami oraz transakcjami.

<h2>Modele:</h2>
<ul>
  <li>Reservation</li>
  <li>Transaction</li>
  <li>Customers</li>
  <li>Room</li>
  <li>Room class</li>
  <li>Room type</li>
</ul>

Addon głównie opiera się na modelu <i>Reservation</i>. Pozwala on na tworzenie rezerwacji odnosząc się do wcześniej utworzonych modeli <i>Room</i> i <i>Customer</i> oraz utworzenie i przypisanie modelu <i>Transaction</i>.

<h2>Mechaniki warte uwagi:</h2>
<ul>
  <li>Podczas tworzenia transakcji za pomocą przycisku w formularzu rezerwacji, formularz transakcji automatycznie wypełnia się danymi i jest gotowy do zapisania.</li><br>

  <li>Po utworzeniu transakcji, transakcja automatycznie jest wykrywana i przypisywana do odpowiedniej rezerwacji zminiając jej właściwość <i>payment status</i>, która jest w pełni zależna od właściwości <i>status</i> przypisanej transakcji.</li><br>

  <li>Podczas przypisywania pokoi do reserwacji można użyć przycisku automatycznego przypisywania, który przypisze pokoje wybranej klasy, idealnie spełniające wymagania jeżeli jest to możliwe, jeżeli nie da się dostać takiej kombinacji, użytkownik zostanie poinformowany o tym alertem.</li><br>

  <li>Rezerwacje i transakcje są w pełni zależne od siebie, usunięcie transakcji spowoduje zmianę właściwości <i>payment status</i> odpowiedniej rezerwacji, a anulowanie rezerwacji oznaczy przypisaną do niej transakcje jako anulowaną.</li><br>

  <!-- <li></li><br> -->


</ul>
